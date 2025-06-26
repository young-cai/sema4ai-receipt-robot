import time
from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(slowmo=100)
    open_robot_order_website()
    orders = get_orders()
    process_orders(orders)
    archive_receipts()

def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def download_orders():
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

def get_orders():
    library = Tables()
    orders = library.read_table_from_csv("orders.csv", columns=["Order number","Head","Body","Legs","Address"])
    return orders

def process_orders(orders):
    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
        preview_order(order)
        submit_order(order)
        press_order_again()

def close_annoying_modal():
    page = browser.page()
    modal = page.wait_for_selector(".modal", timeout=5000)
    close_button = modal.query_selector("button:text('Yep')")
    close_button.click()

def fill_the_form(order):
    page = browser.page()
    order_head = order["Head"] 
    page.select_option("#head", order_head)

    order_body = order["Body"]
    page.locator(f"#id-body-{order_body}").check()

    order_legs = order["Legs"]
    legs_label = page.get_by_text("3. Legs:")
    legs_form_id = legs_label.get_attribute("for")
    page.fill(f"[id='{legs_form_id}']", order_legs)

    order_address = order["Address"]
    page.fill("#address", order_address)

def preview_order(order):
    page = browser.page()
    page.click("button:text('Preview')")

def submit_order(order): 
    page = browser.page()
    order_number = order["Order number"]
    #can add a max-retry in every functino and add an exponential delay on the failed submits
    while True:
        page.click("#order")
        #it is very possible that browser.page does not keep its context, so must do things sequentially
        #lesson learned: perhaps abstraction is bad when you lose the context window
        order_another = page.query_selector("#order-another")
        if order_another:
            receipt_path = store_receipt_as_pdf(order_number)
            screenshot_path = screenshot_robot(order_number)
            embed_screenshot_to_receipt(screenshot_path, receipt_path)
            break

def press_order_again():
    page = browser.page()
    try:
        page.wait_for_selector("#order-another", timeout=500)
        page.click("#order-another")
    except Exception as e:
        print("oh no cant press order again")


def store_receipt_as_pdf(order_number):
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()
    pdf = PDF()
    receipt_path = f"output/receipts/Receipt_Order_{order_number}.pdf"
    pdf.html_to_pdf(receipt_html, receipt_path)
    return receipt_path

def screenshot_robot(order_number):
    page = browser.page()
    robot_preview = page.locator("#robot-preview-image")
    screenshot_path = f"output/screenshots/Screenshot_Order_{order_number}.png"
    if robot_preview and robot_preview.is_visible():
        robot_preview.screenshot(path=screenshot_path)
    return screenshot_path
    
#this one is broken bc of add_files_to_pdf
def embed_screenshot_to_receipt(screenshot_path, receipt_path):
    pdf = PDF()
    #list_of_files = [receipt_path, screenshot]
    pdf.add_watermark_image_to_pdf(image_path=screenshot_path, source_path=receipt_path, output_path=receipt_path)
    #pdf.add_files_to_pdf(files=list_of_files, target_document=receipt_path)
    
    #return receipt_path

def archive_receipts():
    archive = Archive()
    archive.archive_folder_with_zip("output/receipts", "output/receipts_archive.zip")

