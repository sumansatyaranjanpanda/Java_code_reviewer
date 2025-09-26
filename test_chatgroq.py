# test_chatgroq.py
import os, traceback
try:
    from langchain_groq import ChatGroq
    print("Successfully imported ChatGroq")
except Exception as e:
    print("Import error:", e)
    raise

from config.settings import GROQ_API_KEY
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

try:
    # try construction variations
    try:
        client = ChatGroq(model=MODEL, api_key=GROQ_API_KEY)
        print("Constructed ChatGroq(model=..., api_key=...)")
    except Exception as e1:
        print("Constructor with api_key failed:", e1)
        try:
            client = ChatGroq(model=MODEL)
            print("Constructed ChatGroq(model=...)")
        except Exception as e2:
            print("Constructor model-only failed:", e2)
            client = None

    if client is None:
        print("No client instance — stop.")
    else:
        # print the object's dir
        print("\n===== dir(ChatGroq instance) =====")
        for name in sorted(dir(client)):
            print(name)
        print("===== end dir =====\n")

        # try to call a few no-arg accessors safely and print results (wrapped)
        def try_call(attr_name, *args, **kwargs):
            try:
                attr = getattr(client, attr_name)
            except Exception as e:
                print(f"{attr_name}: attribute not found ({e})")
                return
            if callable(attr):
                try:
                    print(f"Trying {attr_name}(...):")
                    out = attr(*args, **kwargs)
                    print(" -> call succeeded. type:", type(out))
                    # print small repr
                    print(repr(out)[:1000])
                except Exception as e:
                    print(f" -> call raised: {e}")
                    tb = traceback.format_exc()
                    print(tb)
            else:
                print(f"{attr_name} is not callable; value repr: {repr(attr)[:500]}")

        # candidate method names we attempted previously
        candidates = [
            "chat", "chat_completion", "chat_completion.create", "create_chat_completion",
            "generate", "create", "invoke", "complete", "completion",
            "__call__", "generate_text"
        ]
        for c in candidates:
            # handle dotted names by attribute lookup
            if "." in c:
                base, sub = c.split(".", 1)
                if hasattr(client, base):
                    obj = getattr(client, base)
                    if hasattr(obj, sub):
                        print(f"Found nested: {base}.{sub} -> callable? {callable(getattr(obj, sub))}")
                    else:
                        print(f"{base}.{sub} not found")
                else:
                    print(f"{base} not found on client")
            else:
                try_call(c)
except Exception as e:
    print("Fatal error in diagnostic:", e)
    traceback.print_exc()
