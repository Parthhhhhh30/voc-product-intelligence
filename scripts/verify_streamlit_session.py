from pathlib import Path
from streamlit.testing.v1 import AppTest

def main():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=60)
    app.run()
    if app.exception:
        raise RuntimeError("Streamlit exceptions: "+" | ".join(str(x.value) for x in app.exception))
    text="\n".join(str(x.value) for x in app.markdown)
    assert "Research the problem" in text
    assert ("Feedback review inbox" in text) or ("Research desk" in text)
    print("STREAMLIT SESSION OK")

if __name__=="__main__":
    main()
