import qrcode

# Generate a QR code for a DIF (link or text)
dif_content = "This is a placeholder for the DIF content or link."
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(dif_content)
qr.make(fit=True)

# Create the image of the QR code
img_path = "/mnt/data/dif_qr_code.png"
img = qr.make_image(fill_color="black", back_color="white")
img.save(img_path)

img_path
