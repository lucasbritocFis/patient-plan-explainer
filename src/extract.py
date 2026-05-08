import pydicom


class ErroValidacaoDICOM(Exception):
    """Erro de validação de arquivo DICOM."""
    pass


def validar_arquivo_dicom(file_obj, modalidade_esperada):
    """
    Valida se o arquivo é DICOM e se tem a modalidade correta.
    Retorna o dataset ou levanta ErroValidacaoDICOM.
    """
    try:
        ds = pydicom.dcmread(file_obj, force=True)
    except Exception:
        raise ErroValidacaoDICOM(
            "O arquivo enviado não parece ser um DICOM válido. "
            "Verifique se é um arquivo .dcm íntegro."
        )

    modalidade = getattr(ds, "Modality", None)
    if modalidade != modalidade_esperada:
        raise ErroValidacaoDICOM(
            f"Esperava um arquivo {modalidade_esperada}, mas recebeu "
            f"'{modalidade or 'desconhecida'}'. Verifique se selecionou o arquivo correto."
        )

    return ds


def _inferir_intencao(plan_ds):
    """Infere se o tratamento é curativo ou paliativo a partir de heurísticas."""
    label = getattr(plan_ds, "RTPlanLabel", "").upper()

    palavras_paliativo = ["PAL", "PALIAT", "META", "OSSEA", "BONE"]
    for palavra in palavras_paliativo:
        if palavra in label:
            return "Paliativo"

    if "DoseReferenceSequence" in plan_ds:
        dose = float(getattr(plan_ds.DoseReferenceSequence[0], "TargetPrescriptionDose", 0))
        if 0 < dose <= 20:
            return "Paliativo (provável)"

    return "Curativo"


def _extrair_energia_feixe(beam):
    """Extrai a energia do feixe formatada (ex: '6 MV', '6 MV FFF')."""
    energia = getattr(beam, "NominalBeamEnergy", None)
    if energia is None:
        return None

    tipo_fluencia = ""
    if "PrimaryFluenceModeSequence" in beam:
        seq = beam.PrimaryFluenceModeSequence
        if len(seq) > 0:
            modo = getattr(seq[0], "FluenceMode", "STANDARD")
            if modo != "STANDARD":
                tipo_fluencia = f" {getattr(seq[0], 'FluenceModeID', 'FFF')}"

    return f"{int(energia)} MV{tipo_fluencia}"


def extrair_dados_completos(file_rtplan, file_rtstruct):
    """
    Lê os arquivos RTPLAN e RTSTRUCT da memória (Streamlit)
    e consolida os dados relevantes para o paciente.
    Levanta ErroValidacaoDICOM se os arquivos forem inválidos.
    """
    dados_paciente = {
        "tecnica_provavel": "Não identificada",
        "intencao_tratamento": "Não identificada",
        "numero_fracoes": 0,
        "dose_total_gy": 0.0,
        "dose_por_fracao_gy": 0.0,
        "energia_feixe": "Não identificada",
        "maquina": "Não identificada",
        "numero_campos": 0,
        "alvos_tecnicos": [],
        "orgaos_protegidos": []
    }

    # --- 1. Extração do RTPLAN ---
    plan_ds = validar_arquivo_dicom(file_rtplan, "RTPLAN")

    dados_paciente["intencao_tratamento"] = _inferir_intencao(plan_ds)

    if "FractionGroupSequence" in plan_ds:
        dados_paciente["numero_fracoes"] = int(
            plan_ds.FractionGroupSequence[0].NumberOfFractionsPlanned
        )

    if "DoseReferenceSequence" in plan_ds:
        dados_paciente["dose_total_gy"] = float(
            plan_ds.DoseReferenceSequence[0].TargetPrescriptionDose
        )

    # Calcular dose por fração
    if dados_paciente["numero_fracoes"] > 0 and dados_paciente["dose_total_gy"] > 0:
        dados_paciente["dose_por_fracao_gy"] = round(
            dados_paciente["dose_total_gy"] / dados_paciente["numero_fracoes"], 2
        )

    if "BeamSequence" in plan_ds:
        campos_tratamento = 0
        is_vmat = False
        is_imrt = False
        energias = set()

        for beam in plan_ds.BeamSequence:
            tipo = getattr(beam, "TreatmentDeliveryType", "TREATMENT")
            if tipo == "TREATMENT":
                campos_tratamento += 1

                # Energia do feixe
                energia = _extrair_energia_feixe(beam)
                if energia:
                    energias.add(energia)

                # Identificação da técnica pela física do feixe
                beam_type = getattr(beam, "BeamType", "")

                if beam_type == "DYNAMIC":
                    if "ControlPointSequence" in beam and len(beam.ControlPointSequence) > 0:
                        cp0 = beam.ControlPointSequence[0]
                        rotacao = getattr(cp0, "GantryRotationDirection", "NONE")

                        if rotacao in ["CW", "CCW"]:
                            is_vmat = True
                        else:
                            is_imrt = True

        dados_paciente["numero_campos"] = campos_tratamento
        dados_paciente["maquina"] = getattr(
            plan_ds.BeamSequence[0], "TreatmentMachineName", "Não identificada"
        )
        dados_paciente["energia_feixe"] = ", ".join(sorted(energias)) or "Não identificada"

        if is_vmat:
            dados_paciente["tecnica_provavel"] = "VMAT (Arcoterapia Volumétrica)"
        elif is_imrt:
            dados_paciente["tecnica_provavel"] = "IMRT (Radioterapia de Intensidade Modulada)"
        else:
            dados_paciente["tecnica_provavel"] = "3D Conformada"

    # Detectar SBRT/hipofracionamento
    if dados_paciente["dose_por_fracao_gy"] >= 6.0 and dados_paciente["numero_fracoes"] <= 8:
        dados_paciente["tecnica_provavel"] += " — SBRT/Hipofracionamento"

    # --- 2. Extração do RTSTRUCT ---
    struct_ds = validar_arquivo_dicom(file_rtstruct, "RTSTRUCT")

    if "StructureSetROISequence" in struct_ds:
        for roi in struct_ds.StructureSetROISequence:
            nome = roi.ROIName
            nome_upper = nome.upper()

            if (nome.startswith("_") or "BODY" in nome_upper
                    or "MESA" in nome_upper or "COUCH" in nome_upper
                    or nome_upper == "AR" or "EXTERNAL" in nome_upper):
                continue
            elif "PTV" in nome_upper or "CTV" in nome_upper or "GTV" in nome_upper:
                dados_paciente["alvos_tecnicos"].append(nome)
            else:
                dados_paciente["orgaos_protegidos"].append(nome)

    return dados_paciente
