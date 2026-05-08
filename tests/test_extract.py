"""Testes unitários para o módulo de extração DICOM."""
import io
import pytest
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.sequence import Sequence
from pydicom.uid import ExplicitVRLittleEndian

from src.extract import extrair_dados_completos, validar_arquivo_dicom, ErroValidacaoDICOM


def _criar_rtplan_minimo(tecnica="VMAT", dose=50.0, fracoes=25):
    """Cria um RTPLAN mínimo em memória para testes."""
    ds = Dataset()
    ds.file_meta = pydicom.dataset.FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.5"
    ds.file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.Modality = "RTPLAN"
    ds.RTPlanLabel = "MAMA_ESQ"

    # Fraction Group
    fg = Dataset()
    fg.NumberOfFractionsPlanned = fracoes
    ds.FractionGroupSequence = Sequence([fg])

    # Dose Reference
    dr = Dataset()
    dr.TargetPrescriptionDose = dose
    ds.DoseReferenceSequence = Sequence([dr])

    # Beam Sequence
    beam = Dataset()
    beam.TreatmentDeliveryType = "TREATMENT"
    beam.TreatmentMachineName = "TrueBeam"
    beam.BeamType = "DYNAMIC"
    beam.NominalBeamEnergy = 6

    fluence = Dataset()
    fluence.FluenceMode = "STANDARD"
    beam.PrimaryFluenceModeSequence = Sequence([fluence])

    cp0 = Dataset()
    if tecnica == "VMAT":
        cp0.GantryRotationDirection = "CW"
    else:
        cp0.GantryRotationDirection = "NONE"
    beam.ControlPointSequence = Sequence([cp0])

    ds.BeamSequence = Sequence([beam])

    buf = io.BytesIO()
    pydicom.dcmwrite(buf, ds, write_like_original=False)
    buf.seek(0)
    return buf


def _criar_rtstruct_minimo(rois=None):
    """Cria um RTSTRUCT mínimo em memória para testes."""
    ds = Dataset()
    ds.file_meta = pydicom.dataset.FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.3"
    ds.file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.Modality = "RTSTRUCT"

    if rois is None:
        rois = ["PTV_50", "CTV_mama", "Coracao", "Pulmao_E", "BODY"]

    roi_seq = []
    for i, nome in enumerate(rois):
        roi = Dataset()
        roi.ROINumber = i + 1
        roi.ROIName = nome
        roi_seq.append(roi)
    ds.StructureSetROISequence = Sequence(roi_seq)

    buf = io.BytesIO()
    pydicom.dcmwrite(buf, ds, write_like_original=False)
    buf.seek(0)
    return buf


# --- Testes de validação ---

def test_validar_arquivo_nao_dicom():
    """Arquivo não-DICOM deve levantar ErroValidacaoDICOM (modalidade desconhecida)."""
    fake = io.BytesIO(b"isso nao e dicom")
    with pytest.raises(ErroValidacaoDICOM):
        validar_arquivo_dicom(fake, "RTPLAN")


def test_validar_modalidade_errada():
    """RTSTRUCT enviado como RTPLAN deve ser rejeitado."""
    rtstruct = _criar_rtstruct_minimo()
    with pytest.raises(ErroValidacaoDICOM, match="Esperava um arquivo RTPLAN"):
        validar_arquivo_dicom(rtstruct, "RTPLAN")


# --- Testes de extração VMAT ---

def test_extracao_vmat_basica():
    """RTPLAN VMAT deve retornar técnica, dose e frações corretas."""
    plan = _criar_rtplan_minimo(tecnica="VMAT", dose=50.0, fracoes=25)
    struct = _criar_rtstruct_minimo()
    dados = extrair_dados_completos(plan, struct)

    assert "VMAT" in dados["tecnica_provavel"]
    assert dados["dose_total_gy"] == 50.0
    assert dados["numero_fracoes"] == 25
    assert dados["dose_por_fracao_gy"] == 2.0
    assert dados["maquina"] == "TrueBeam"


def test_extracao_imrt():
    """Beam dinâmico sem rotação deve ser classificado como IMRT."""
    plan = _criar_rtplan_minimo(tecnica="IMRT", dose=66.0, fracoes=33)
    struct = _criar_rtstruct_minimo()
    dados = extrair_dados_completos(plan, struct)

    assert "IMRT" in dados["tecnica_provavel"]


# --- Testes de extração RTSTRUCT ---

def test_filtra_body_e_classifica_rois():
    """BODY deve ser filtrado; PTV/CTV vão pra alvos, resto pra órgãos."""
    plan = _criar_rtplan_minimo()
    struct = _criar_rtstruct_minimo(["PTV_50", "CTV_mama", "Coracao", "Pulmao_E", "BODY"])
    dados = extrair_dados_completos(plan, struct)

    assert "BODY" not in str(dados["alvos_tecnicos"])
    assert "BODY" not in str(dados["orgaos_protegidos"])
    assert "PTV_50" in dados["alvos_tecnicos"]
    assert "CTV_mama" in dados["alvos_tecnicos"]
    assert "Coracao" in dados["orgaos_protegidos"]
    assert "Pulmao_E" in dados["orgaos_protegidos"]


# --- Teste de SBRT ---

def test_deteccao_sbrt():
    """Hipofracionamento extremo deve ser identificado como SBRT."""
    plan = _criar_rtplan_minimo(tecnica="VMAT", dose=54.0, fracoes=3)
    struct = _criar_rtstruct_minimo()
    dados = extrair_dados_completos(plan, struct)

    assert "SBRT" in dados["tecnica_provavel"]


# --- Teste de energia ---

def test_energia_feixe():
    """Energia do feixe deve ser extraída."""
    plan = _criar_rtplan_minimo()
    struct = _criar_rtstruct_minimo()
    dados = extrair_dados_completos(plan, struct)

    assert "6 MV" in dados["energia_feixe"]
