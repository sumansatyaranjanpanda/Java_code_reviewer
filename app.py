# app.py
import streamlit as st
from core.schema import Response
from core.graph import workflow

st.set_page_config(page_title="Simple Java Review", layout="wide")
st.title("Simple Multi-Agent Java Review — Minimal")
st.write("Paste or upload Java code. App runs 10 parallel checks and shows two outputs: final suggestions and final updated code.")

uploaded = st.file_uploader("Upload Java file", type=["java"], key="upload")
pasted = st.text_area("Or paste Java code (overrides upload)", height=300, key="paste")

if st.button("Run review"):
    code = None
    filename = "pasted.java"
    if pasted and pasted.strip():
        code = pasted
    elif uploaded:
        try:
            code = uploaded.getvalue().decode("utf-8")
            filename = uploaded.name
        except Exception:
            code = uploaded.getvalue().decode("latin-1")
            filename = uploaded.name
    else:
        st.error("Provide Java code by uploading or pasting.")
        st.stop()

    st.info("Running 10 guideline agents in parallel then merging — please wait.")
    init_state = Response(code_snippet=code)
    try:
        final_state = workflow.invoke(init_state)
    except Exception as e:
        st.error(f"Workflow invocation failed: {e}")
        st.stop()

    # fetch merged suggestions and final code (state may be dict or pydantic)
    if isinstance(final_state, dict):
        merge_text = final_state.get("merge_guide_res", "")
        final_code = final_state.get("final_updated_code", "")
    else:
        merge_text = getattr(final_state, "merge_guide_res", "") or ""
        final_code = getattr(final_state, "final_updated_code", "") or ""

    # 🎉 Balloons on success
    if (merge_text and merge_text.strip()) or (final_code and final_code.strip()):
        st.success("Review completed — results below 🎉")
        st.balloons()
    else:
        st.info("Review completed but no suggestions/final code were produced.")

    # # 🖼️ Sidebar: workflow diagram
    # try:
    #     # if your `workflow` object has a compiled graph with draw_mermaid_png
    #     compiled_graph = workflow  # adjust if you have workflow.compile() or similar
    #     graph_png = compiled_graph.get_graph().draw_mermaid_png()
    #     st.sidebar.image(graph_png, caption="Workflow Graph", use_column_width=True)
    # except Exception as e:
    #     st.sidebar.warning(f"Could not render workflow graph: {e}")

    # Main outputs
    st.markdown("## Final consolidated suggestions")
    st.text_area("Final suggestions (LLM)", value=(merge_text or "No suggestions produced."), height=300, key="final_sugg")

    st.markdown("## Final updated code")
    st.code(final_code or "// no final code produced", language="java", line_numbers=True)
    st.download_button("Download final code", final_code or "", file_name=f"final_{filename}", key="dl_final")
