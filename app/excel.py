import pandas as pd
import mysql.connector
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode

# --- DB CONFIG ---
USERNAME = 'SVEnterprise'
DBPASS = 'SVE@DB21'
DBNAME = 'SVEnterprise$sv'

# --- Excel File ---
excel_path = '/home/SVEnterprise/SVEnterprise/app/static/images/employees1.xlsx'

# --- Font Loader ---
def load_fonts():
    font_dir = "/home/SVEnterprise/SVEnterprise/app/fonts"
    bold_path = os.path.join(font_dir, "Poppins-Bold.ttf")
    reg_path = os.path.join(font_dir, "Poppins-Regular.ttf")

    try:
        title_font = ImageFont.truetype(bold_path, 35)
        bold_font = ImageFont.truetype(bold_path, 30)
        text_font = ImageFont.truetype(reg_path, 25)
        print("✅ Fonts loaded successfully.")
    except IOError:
        print("⚠️ Font files not found. Using default system font.")
        title_font = bold_font = text_font = ImageFont.load_default()

    return title_font, bold_font, text_font

# --- Justified Text ---
def draw_justified_text(draw, text, position, font, max_width, bold_name=None):
    words = text.split()
    lines, line, line_width = [], [], 0
    space_w = draw.textbbox((0, 0), " ", font=font)[2]

    for word in words:
        w = draw.textbbox((0, 0), word, font=font)[2]
        if line and line_width + w + space_w > max_width:
            lines.append((line, line_width))
            line, line_width = [], 0
        line.append(word)
        line_width += w + (space_w if line else 0)
    if line:
        lines.append((line, line_width))

    y = position[1]
    for ln, ln_w in lines:
        if len(ln) == 1:
            draw.text((position[0], y), ln[0], fill="black", font=font)
        else:
            total_spacing = max_width - ln_w
            extra = total_spacing // (len(ln) - 1)
            x = position[0]
            for word in ln[:-1]:
                f = font_bold if bold_name and word == bold_name else font
                draw.text((x, y), word, fill="black", font=f)
                x += draw.textbbox((0, 0), word, font=f)[2] + space_w + extra
            draw.text((x, y), ln[-1], fill="black", font=font_bold if bold_name and ln[-1] == bold_name else font)
        y += font.getbbox("A")[3] - font.getbbox("A")[1] + 10

# --- ID Card Generator ---
def create_id_card(employee_data):
    W, H = 600, 980
    card = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(card)
    global font_bold
    font_title, font_bold, font_text = load_fonts()

    logo_path = "/home/SVEnterprise/SVEnterprise/app/static/assets/logo.jpg"
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).resize((400, 80))
        card.paste(logo, ((W - 400) // 2, 20))

    draw.text((13, 120), "AUTHORIZED COLLECTION AGENT", fill="black", font=font_title)

    card.paste(employee_data["Photo"].resize((180, 180)), (210, 180))

    y = 380
    for label, value in [
        ("Name", employee_data["Name"]),
        ("Designation", employee_data["Designation"]),
        ("Phone No.", employee_data["Phone No."]),
        ("ID Card No", employee_data["ID Card No"]),
    ]:
        draw.text((50, y), f"{label}:", fill="black", font=font_text)
        draw.text((250, y), str(value), fill="black", font=font_bold)
        y += 40

    para = (
        "TO WHOMSOEVER IT MAY CONCERN\n\n"
        f"This is to certify that {employee_data['Name']} is an employee of\n"
        "S V ENTERPRISES. They are authorized to collect\n"
        "money (Cash, Cheques, or Demand Drafts) from customers,\n"
        "provided that a valid receipt is issued in return."
    )
    draw_justified_text(draw, para, (50, y + 20), font_text, 500, bold_name=employee_data["Name"])

    qr_data = (
        f"ID: {employee_data['ID Card No']}\n"
        f"Name: {employee_data['Name']}\n"
        f"Designation: {employee_data['Designation']}\n"
        f"Phone: {employee_data['Phone No.']}\n"
        f"Blood Group: {employee_data['Blood Group']}\n"
        f"Date of Joining: {employee_data['Date of Joining']}"
    )
    qr = qrcode.QRCode(box_size=5, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    card.paste(qr.make_image(fill="black", back_color="white").resize((150, 150)), (220, 820))

    return card

# --- Excel Reading ---
df = pd.read_excel(excel_path).rename(columns={
    'Employee ID': 'emp_id',
    'Name': 'name',
    'Designation': 'designation',
    'Phone No.': 'phoneno',
    'Photo': 'photo_path',
    'Do you have KYC compliance?': 'status',
    'Date of Issue': 'doi',
    'Enter your Blood Group': 'bloodgrp',
    'Email': 'email'
})

# --- DB Connect ---
conn = mysql.connector.connect(
    host=f'{USERNAME}.mysql.pythonanywhere-services.com',
    user=USERNAME,
    password=DBPASS,
    database=DBNAME
)
cursor = conn.cursor()

query = """
INSERT INTO employees
(emp_id, email, status, name, phoneno, designation, bloodgrp, doi, idcard)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

records = []

for _, row in df.iterrows():
    try:
        photo_path = str(row['photo_path']).strip().replace('"', '').replace("'", '')
        if not photo_path.startswith("/"):
            photo_path = os.path.join("/home/SVEnterprise/SVEnterprise/app/static/images", os.path.basename(photo_path))

        with Image.open(photo_path).convert("RGB") as img:
            # Optional resize to avoid massive BLOBs
            img = img.resize((180, 180))

            employee_data = {
                "Photo": img,
                "Name": row["name"],
                "Designation": row["designation"],
                "Phone No.": row["phoneno"],
                "ID Card No": row["emp_id"],
                "Blood Group": row["bloodgrp"],
                "Date of Joining": row["doi"]
            }

            idcard_img = create_id_card(employee_data)
            buffer = BytesIO()
            idcard_img = idcard_img.resize((600, 980))  # resize final output
            idcard_img.save(buffer, format='JPEG', quality=60)  # compression
            image_bytes = buffer.getvalue()

        records.append((
            row["emp_id"],
            row["email"],
            row["status"],
            row["name"],
            row["phoneno"],
            row["designation"],
            row["bloodgrp"],
            row["doi"],
            image_bytes
        ))
    except Exception as e:
        print(f"❌ Error for {row['emp_id']}: {e}")

# --- Final DB Insert ---
try:
    cursor.executemany(query, records)
    conn.commit()
    print(f"✅ {cursor.rowcount} employees inserted.")
except Exception as e:
    print("❌ Database insert error:", e)
    conn.rollback()

cursor.close()
conn.close()
