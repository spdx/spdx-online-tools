# -*- coding: utf-8 -*-


from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time

from django.conf import settings
import os


def getExamplePath(filename):
    return os.path.join(settings.EXAMPLES_DIR, filename)


class LicenseXMLEditorTestCase(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument('-headless')
        self.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_options=options)
        self.initialXML = '<?xml version="1.0" encoding="UTF-8"?><SPDXLicenseCollection xmlns="http://www.spdx.org/license"><license></license></SPDXLicenseCollection>'
        self.invalidXML = '<?xml version="1.0" encoding="UTF-8"?><SPDXLicenseCollection xmlns="http://www.spdx.org/license"><license></license>'
        super(LicenseXMLEditorTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(LicenseXMLEditorTestCase, self).tearDown()

    def test_tree_editor_attributes(self):
        """ Test for adding, editing and deleting attributes using tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabTreeEditor").click()
        """ Adding attribute """
        driver.find_element_by_xpath("/html/body/div[2]/div/div[2]/div/ul/li/ul/li[3]/img[3]").click()
        driver.find_element_by_class_name("newAttributeName").send_keys("firstAttribute")
        driver.find_element_by_class_name("newAttributeValue").send_keys("firstValue")
        driver.find_element_by_class_name("addNewAttribute").click()
        """ Adding Invalid attribute """
        driver.find_element_by_xpath("/html/body/div[2]/div/div[2]/div/ul/li/ul/li[3]/img[3]").click()
        driver.find_element_by_class_name("newAttributeName").send_keys("secondAttribute")
        driver.find_element_by_class_name("addNewAttribute").click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEqual(modal_text, "Please enter valid attribute name and value")
        driver.find_element_by_css_selector("div.modal-footer button.btn").click()
        time.sleep(0.5)
        driver.find_element_by_class_name("newAttributeValue").send_keys("secondValue")
        driver.find_element_by_class_name("cancel").click()
        """ Editing attribute """
        driver.find_elements_by_css_selector("span.attributeValue")[1].click()
        driver.find_element_by_css_selector("input.textbox").clear()
        driver.find_element_by_css_selector("input.textbox").send_keys("Edited Value")
        driver.find_element_by_css_selector("img.editAttribute").click()
        editedValue = driver.find_elements_by_css_selector("span.attributeValue")[1].text
        self.assertEqual(editedValue, "Edited Value")
        """ Delete attribute """
        driver.find_elements_by_css_selector("span.attributeValue")[1].click()
        driver.find_element_by_css_selector("img.removeAttribute").click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEqual(modal_text, "Are you sure you want to delete this attribute? This action cannot be undone.")
        driver.find_element_by_id("modalOk").click()
        time.sleep(0.5)
        driver.find_element_by_id("tabTextEditor").click()
        codemirror = driver.find_elements_by_css_selector("pre.CodeMirror-line")
        time.sleep(0.2)
        finalXML = ""
        for i in codemirror:
            finalXML += i.text.strip()
        self.assertEqual(self.initialXML, finalXML)

    def test_split_tree_editor_attributes(self):
        """ Test for adding, editing and deleting attributes using split view tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to split view """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabSplitView").click()
        """ Adding attribute """
        driver.execute_script("document.getElementsByClassName('addAttribute')[1].click()")
        driver.execute_script("document.getElementsByClassName('newAttributeName')[0].value = 'firstAttribute'")
        driver.execute_script("document.getElementsByClassName('newAttributeValue')[0].value = 'firstValue'")
        driver.execute_script("document.getElementsByClassName('addNewAttribute')[0].click()")
        """ Adding Invalid attribute """
        driver.execute_script("document.getElementsByClassName('addAttribute')[1].click()")
        driver.execute_script("document.getElementsByClassName('newAttributeName')[0].value = 'secondAttribute'")
        driver.execute_script("document.getElementsByClassName('addNewAttribute')[0].click()")
        modal_text = driver.execute_script("return document.getElementById('modal-body').innerHTML")
        self.assertEqual(modal_text, "Please enter valid attribute name and value")
        driver.execute_script("document.querySelector('div.modal-footer button.btn').click()")
        time.sleep(0.5)
        driver.execute_script("document.getElementsByClassName('newAttributeValue')[0].value = 'secondValue'")
        driver.execute_script("document.getElementsByClassName('cancel')[0].click()")
        """ Editing attribute """
        driver.execute_script("document.querySelectorAll('span.attributeValue')[1].click()")
        driver.execute_script("document.querySelector('input.textbox').value = ''")
        driver.execute_script("document.querySelector('input.textbox').value = 'Edited Value'")
        driver.execute_script("document.querySelector('img.editAttribute').click()")
        editedValue = driver.find_elements_by_css_selector("span.attributeValue")[1].text
        self.assertEqual(editedValue, "Edited Value")
        """ Delete attribute """
        driver.execute_script("document.querySelectorAll('span.attributeValue')[1].click()")
        driver.execute_script("document.querySelector('img.removeAttribute').click()")
        modal_text = driver.execute_script("return document.getElementById('modal-body').innerHTML")
        self.assertEqual(modal_text, "Are you sure you want to delete this attribute? This action cannot be undone.")
        driver.execute_script("document.getElementById('modalOk').click()")
        time.sleep(0.5)
        driver.execute_script("document.getElementById('tabTextEditor').click()")
        finalXML = driver.execute_script("var xml = ''; var codemirror = document.querySelectorAll('pre.CodeMirror-line'); for (var i=1;i<(codemirror.length/2)-1;i++){xml = xml + codemirror[i].textContent.trim();} return xml;")
        time.sleep(0.2)
        self.assertEqual(self.initialXML, finalXML)

    def test_tree_editor_nodes(self):
        """ Test for adding and deleting nodes(tags) using tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabTreeEditor").click()
        """ Adding node """
        driver.find_element_by_css_selector("li.addChild.last").click()
        driver.find_element_by_css_selector("input.textbox").send_keys("newNode")
        driver.find_element_by_class_name("buttonAddChild").click()
        """ Adding invalid node """
        driver.find_element_by_css_selector("li.addChild.last").click()
        driver.find_element_by_class_name("buttonAddChild").click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEqual(modal_text, "The tag name cannot be empty. Please enter a valid tag name.")
        driver.find_element_by_css_selector("div.modal-footer button.btn").click()
        time.sleep(0.5)
        driver.find_element_by_class_name("cancelAddChild").click()
        """ Delete attribute """
        driver.find_elements_by_css_selector("img.deleteNode")[2].click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEqual(modal_text, "Are you sure you want to delete this tag? This cannot be undone.")
        driver.find_element_by_id("modalOk").click()
        time.sleep(0.5)
        driver.find_element_by_id("tabTextEditor").click()
        codemirror = driver.find_elements_by_css_selector("pre.CodeMirror-line")
        finalXML = ""
        for i in codemirror:
            finalXML += i.text.strip()
        self.assertEqual(self.initialXML, finalXML)

    def test_split_tree_editor_nodes(self):
        """ Test for adding and deleting nodes(tags) using split view tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to split view """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabSplitView").click()
        """ Adding node """
        driver.execute_script("document.querySelectorAll('li.addChild.last')[1].click()")
        driver.execute_script("document.querySelector('input.textbox').value = 'newNode'")
        driver.execute_script("document.getElementsByClassName('buttonAddChild')[0].click()")
        """ Adding invalid node """
        driver.execute_script("document.querySelectorAll('li.addChild.last')[1].click()")
        driver.execute_script("document.getElementsByClassName('buttonAddChild')[0].click()")
        modal_text = driver.execute_script("return document.getElementById('modal-body').innerHTML")
        self.assertEqual(modal_text, "The tag name cannot be empty. Please enter a valid tag name.")
        driver.execute_script("document.querySelector('div.modal-footer button.btn').click()")
        time.sleep(0.5)
        driver.execute_script("document.getElementsByClassName('cancelAddChild')[0].click()")
        """ Delete attribute """
        driver.execute_script("document.querySelectorAll('img.deleteNode')[2].click()")
        modal_text = driver.execute_script("return document.getElementById('modal-body').innerHTML")
        self.assertEqual(modal_text, "Are you sure you want to delete this tag? This cannot be undone.")
        driver.execute_script("document.getElementById('modalOk').click()")
        time.sleep(0.5)
        driver.execute_script("document.getElementById('tabTextEditor').click()")
        finalXML = driver.execute_script("var xml = ''; var codemirror = document.querySelectorAll('pre.CodeMirror-line'); for (var i=1;i<(codemirror.length/2)-1;i++){xml = xml + codemirror[i].textContent.trim();} return xml;")
        time.sleep(0.2)
        self.assertEqual(self.initialXML, finalXML)

    def test_tree_editor_text(self):
        """ Test for adding, editing and deleting text inside tags using tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabTreeEditor").click()
        """ Adding text """
        driver.find_element_by_css_selector("li.emptyText").click()
        driver.find_element_by_css_selector("div.treeContainer textarea").send_keys("This is some sample text.")
        driver.find_element_by_class_name("editNodeText").click()
        nodeText = driver.find_element_by_css_selector("li.nodeText").text
        self.assertEqual(nodeText, "This is some sample text.")
        """ Editing text """
        driver.find_element_by_css_selector("li.nodeText").click()
        driver.find_element_by_css_selector("div.treeContainer textarea").clear()
        driver.find_element_by_css_selector("div.treeContainer textarea").send_keys("Edited text.")
        driver.find_element_by_class_name("editNodeText").click()
        nodeText = driver.find_element_by_css_selector("li.nodeText").text
        self.assertEqual(nodeText, "Edited text.")
        """ Delete text """
        driver.find_element_by_css_selector("li.nodeText").click()
        driver.find_element_by_css_selector("div.treeContainer textarea").clear()
        driver.find_element_by_class_name("editNodeText").click()
        nodeText = driver.find_element_by_css_selector("li.emptyText").text
        self.assertEqual(nodeText, "(No text value. Click to edit.)")
        driver.find_element_by_id("tabTextEditor").click()
        codemirror = driver.find_elements_by_css_selector("pre.CodeMirror-line")
        finalXML = ""
        for i in codemirror:
            finalXML += i.text.strip()
        self.assertEqual(self.initialXML, finalXML)

    def test_split_tree_editor_text(self):
        """ Test for adding, editing and deleting text inside tags using split view tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to split view """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabSplitView").click()
        """ Adding text """
        driver.execute_script("document.querySelectorAll('li.emptyText')[1].click()")
        driver.execute_script("document.querySelectorAll('li.emptyText')[1].click()")
        driver.execute_script("document.querySelector('ul textarea').value = 'This is some sample text.'")
        driver.execute_script("document.getElementsByClassName('editNodeText')[0].click()")
        nodeText = driver.execute_script("return document.querySelector('li.nodeText').innerHTML")
        self.assertEqual(nodeText, "This is some sample text.")
        """ Editing text """
        driver.execute_script("document.querySelectorAll('li.nodeText')[0].click()")
        driver.execute_script("document.querySelector('ul textarea').value = ''")
        driver.execute_script("document.querySelector('ul textarea').value = 'Edited text.'")
        driver.execute_script("document.getElementsByClassName('editNodeText')[0].click()")
        nodeText = driver.execute_script("return document.querySelector('li.nodeText').innerHTML")
        self.assertEqual(nodeText, "Edited text.")
        """ Delete text """
        driver.execute_script("document.querySelectorAll('li.nodeText')[0].click()")
        driver.execute_script("document.querySelector('ul textarea').value = ''")
        driver.execute_script("document.getElementsByClassName('editNodeText')[0].click()")
        nodeText = driver.execute_script("return document.querySelector('li.emptyText').innerHTML")
        self.assertEqual(nodeText, "(No text value. Click to edit.)")
        driver.execute_script("document.getElementById('tabTextEditor').click()")
        finalXML = driver.execute_script("var xml = ''; var codemirror = document.querySelectorAll('pre.CodeMirror-line'); for (var i=1;i<(codemirror.length/2)-1;i++){xml = xml + codemirror[i].textContent.trim();} return xml;")
        time.sleep(0.2)
        self.assertEqual(self.initialXML, finalXML)

    def test_tree_editor_invalid_xml(self):
        """ Test for invalid XML text provided """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_id("xmltext").send_keys(self.invalidXML)
        driver.find_element_by_id("xmlTextButton").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabTreeEditor").click()
        """ Checking for error message """
        error_title = driver.find_element_by_css_selector("h2.xmlParsingErrorMessage").text
        error_message = driver.find_element_by_css_selector("span.xmlParsingErrorMessage").text
        self.assertEqual(error_title, "Invalid XML.")
        assert "XML Parsing Error" in error_message

    def test_split_tree_editor_invalid_xml(self):
        """ Test for invalid XML text provided """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_id("xmltext").send_keys(self.invalidXML)
        driver.find_element_by_id("xmlTextButton").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabSplitView").click()
        """ Checking for error message """
        error_title = driver.find_element_by_css_selector("h2.xmlParsingErrorMessage").text
        error_message = driver.find_element_by_css_selector("span.xmlParsingErrorMessage").text
        self.assertEqual(error_title, "Invalid XML.")
        assert "XML Parsing Error" in error_message
