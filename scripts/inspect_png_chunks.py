import struct

def inspect_png_chunks(fpath):
    with open(fpath, "rb") as f:
        sig = f.read(8)
        assert sig == b"\x89PNG\r\n\x1a\n", "Not a valid PNG"
        chunks = []
        while True:
            length_bytes = f.read(4)
            if not length_bytes:
                break
            length = struct.unpack(">I", length_bytes)[0]
            chunk_type = f.read(4)
            data = f.read(length)
            crc = f.read(4)
            chunks.append((chunk_type.decode("latin1", errors="replace"), length))
            if chunk_type in [b"tEXt", b"zTXt", b"iTXt"]:
                print(f"  Text chunk: {chunk_type} -> {data[:100]}")
    print(f"Chunks in {fpath}:", chunks)

inspect_png_chunks("dataset/evidence/images/account_admin_console_20260926.png")
inspect_png_chunks("dataset/evidence/images/marketing_profile_console.png")
