import zipfile, base64, qrcode, os, math, argparse
from fpdf import FPDF

def create_pdf(b64_chunks, file_name, cmd, dpi, mod_px):
    pdf = FPDF()
    pdf.set_auto_page_break(False)
    
    mm_per_inch = 25.4
    mod_size_mm = (mod_px / dpi) * mm_per_inch
    
    margin_left, margin_top = 10, 15
    spacing = 2  # Minimaler Abstand zwischen den Codes
    current_x, current_y = margin_left, margin_top
    max_row_height = 0
    total = len(b64_chunks)
    
    pdf.add_page()
    pdf.set_font("Courier", size=8)
    pdf.text(10, 8, f"FILE: {file_name} | {total} Chunks | {dpi} DPI | Mod: {mod_px}px")

    for i, payload in enumerate(b64_chunks):
        qr = qrcode.QRCode(box_size=1, border=4, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(payload)
        qr.make(fit=True)
        qr_size_mm = qr.modules_count * mod_size_mm
        
        # Zeilenumbruch prüfen
        if current_x + qr_size_mm > 200:
            current_x = margin_left
            current_y += max_row_height + spacing
            max_row_height = 0
            
        # Seitenumbruch prüfen
        if current_y + qr_size_mm > 280:
            pdf.add_page()
            current_x, current_y = margin_left, margin_top
            max_row_height = 0

        img = qr.make_image()
        qr_path = f"tmp_{i}.png"
        img.save(qr_path)
        
        # Bild platzieren ohne Index-Text darunter
        pdf.image(qr_path, x=current_x, y=current_y, w=qr_size_mm)
        
        max_row_height = max(max_row_height, qr_size_mm)
        current_x += qr_size_mm + spacing
        os.remove(qr_path)

    # Recovery-Befehl am Ende
    final_y = current_y + max_row_height + 10
    if final_y > 275: 
        pdf.add_page()
        final_y = 20
        
    pdf.set_xy(margin_left, final_y)
    pdf.set_font("Courier", "B", size=8)
    pdf.multi_cell(190, 5, f"RECOVERY CMD:\n{cmd}")

    out_name = f"{file_name}_clean.pdf"
    pdf.output(out_name)
    print(f"\nPDF erstellt: {out_name}")

def process_file(file_path, chunk_size, dpi, mod_px):
    if not os.path.exists(file_path): return
    with zipfile.ZipFile("temp.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(file_path, os.path.basename(file_path))
    with open("temp.zip", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.remove("temp.zip")

    total = math.ceil(len(b64) / chunk_size)
    chunks = [f"{i+1}/{total}:{b64[i*chunk_size : (i+1)*chunk_size]}" for i in range(total)]
    cmd = "sort -V qr-scan.txt | sed 's/^[0-9]*\\/[0-9]*://' | tr -d '\\n ' | base64 -d > out.zip"

    print(f"Datei: {file_path} | Chunks: {total} | {dpi} DPI | Modul: {mod_px}px")
    if input("PDF generieren? (j/n): ").lower() == 'j':
        create_pdf(chunks, os.path.basename(file_path), cmd, dpi, mod_px)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("-s", "--size", type=int, default=800)
    parser.add_argument("-d", "--dpi", type=int, default=600)
    parser.add_argument("-m", "--module", type=int, default=5)
    args = parser.parse_args()
    process_file(args.input, args.size, args.dpi, args.module)
