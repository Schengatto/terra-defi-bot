from fpdf import FPDF


class PDF(FPDF):
    pass


def create_pdf(title, orientation='P', format='A4'):
    pdf = PDF(orientation=orientation, format=format)
    add_page(pdf)
    pdf.set_author('Ftool')
    add_title(pdf, title)
    pdf.set_y(30)
    return pdf


def save_pdf(pdf, name, path="./"):
    pdf.output(f'{path}{name}.pdf', 'F')
    pdf.close()


def add_page(pdf):
    pdf.add_page()


def add_title(pdf, title):
    pdf.set_xy(0.0, 0.0)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(220, 50, 50)
    pdf.cell(w=210.0, h=40.0, align='C', txt=title, border=0)


def add_text_row(pdf, text, y_pos=None, x_pos=10.0, color=(0, 0, 0)):
    if y_pos is None:
        y_pos = pdf.get_y() + 10

    pdf.set_xy(x_pos, y_pos)
    pdf.set_text_color(*color)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, text)


def add_image(pdf, image_path, width=190, height=100, y_pos=None, x_pos=10.0):
    if y_pos is None:
        y_pos = pdf.get_y() + 10

    pdf.image(image_path, link='', type='', w=width, h=height, x=x_pos, y=y_pos)
    pdf.set_y(y_pos + height + 10)


def generate_pdf(file_name, title="Report", text_rows=["Text here"], images=[]):
    pdf = create_pdf(title)
    for text in text_rows:
        add_text_row(pdf, text)

    for image in images:
        add_image(pdf, image, 190, 100)

    save_pdf(pdf, file_name)
