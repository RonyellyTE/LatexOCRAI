import re 
import fitz
from PIL import Image
import io

def extract_images(pdf, page_num, page):
    images_list = []
    try:
        images = page.get_images()
        if images:
            for index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = pdf.extract_image(xref)
                image_data = base_image["image"] 
                try:
                    image = Image.open(io.BytesIO(image_data))
                    image_filename = f"images/pagina{page_num}_imagem{index}.png"
                    image = image.convert("RGB")
                    image.save(image_filename)
                    images_list.append(image_filename)
                except Exception as image_error:
                    print(f"Erro ao processar imagem {index} na página {page_num}: {image_error}")
    except Exception as extraction_error:
        print(f"Erro ao extrair imagens da página {page_num}: {extraction_error}")

    return images_list


def ia_conversation_text_pdf(pdf, ):
        text_pages = ""
        for page_number in range(len(pdf)):
            page_text = ""
            page = pdf[page_number]
            page_img = extract_images(pdf, page_number, page)
            for block_extracted1 in page.get_text("blocks"):
                paragraph = block_extracted1[4]
                print(paragraph)
                padrao = r"<image: [^>]*width: [^>]*height: [^>]*bpc: [^>]*>"
                resultado = re.findall(padrao, paragraph)
                if resultado and page_img:
                    page_text += r"""\begin{figure}
  \centering
  \includegraphics[width=0.8\linewidth]{%s}
  \caption{Sua legenda aqui}
  \label{fig:suafigura}
\end{figure}
""" % page_img.pop(0)
                else:
                    page_text += paragraph

            text_pages += page_text

        return text_pages
