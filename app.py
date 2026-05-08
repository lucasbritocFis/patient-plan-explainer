import streamlit as st

# Nossas funções construídas na pasta src
from src.extract import extrair_dados_completos, ErroValidacaoDICOM
from src.narrate import gerar_explicacao_paciente
from src.export import gerar_pdf, gerar_audio

st.set_page_config(
    page_title="Explicador de Plano de Tratamento | Radioterapia",
    page_icon="🎯",
    layout="centered"
)

def main():
    st.title("Explicador de Plano de Tratamento")
    st.markdown("Transforme dados técnicos do DICOM em explicações claras, áudio e PDF para seus pacientes.")
    st.divider()

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**1. Arquivo do Plano (RTPLAN)**")
        rtplan_file = st.file_uploader("Suba o RTPLAN (.dcm)", type=['dcm'], key="plan")
        
    with col2:
        st.markdown("**2. Arquivo de Estruturas (RTSTRUCT)**")
        rtstruct_file = st.file_uploader("Suba o RTSTRUCT (.dcm)", type=['dcm'], key="struct")

    st.divider()

    if st.button("Gerar Explicação Completa", type="primary", use_container_width=True):
        if not rtplan_file or not rtstruct_file:
            st.warning("⚠️ Por favor, suba ambos os arquivos (RTPLAN e RTSTRUCT) antes de continuar.")
        else:
            try:
                # 1: Extração
                with st.spinner("Lendo arquivos DICOM..."):
                    dados_extraidos = extrair_dados_completos(rtplan_file, rtstruct_file)

                # 2: Geração do Texto (IA)
                with st.spinner("Inteligência Artificial redigindo o texto..."):
                    texto_paciente = gerar_explicacao_paciente(dados_extraidos)

                if texto_paciente.startswith("⚠️"):
                    st.error(texto_paciente)
                else:
                    st.success("Tudo pronto!")
                    st.markdown("### Mensagem para o Paciente")
                    st.info(texto_paciente)

                    st.divider()

                    # --- FASE 3: EXPORTAÇÃO (PDF e ÁUDIO) ---
                    st.markdown("### 📥 Entregáveis para o Paciente")

                    col_audio, col_pdf = st.columns(2)

                    with col_audio:
                        st.markdown("**Ouvir a explicação:**")
                        with st.spinner("Gerando áudio..."):
                            audio_buffer, audio_mime = gerar_audio(texto_paciente)
                            st.audio(audio_buffer, format=audio_mime)

                    with col_pdf:
                        st.markdown("**Imprimir documento:**")
                        with st.spinner("Gerando PDF..."):
                            pdf_bytes = gerar_pdf(texto_paciente, dados_extraidos)
                            st.download_button(
                                label="📄 Baixar Resumo em PDF",
                                data=pdf_bytes,
                                file_name="Resumo_Tratamento_Radioterapia.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )

                    # Dados técnicos escondidos
                    with st.expander("Ver dados técnicos extraídos do DICOM"):
                        st.json(dados_extraidos)

            except ErroValidacaoDICOM as e:
                st.error(f"Problema com o arquivo DICOM: {e}")
            except Exception:
                st.error(
                    "Ocorreu um erro inesperado. Verifique se os arquivos são "
                    "DICOMs válidos e tente novamente."
                )

if __name__ == "__main__":
    main()