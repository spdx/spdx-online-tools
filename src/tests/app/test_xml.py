# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for XML upload, validation, and XML editor views.
"""

import time
from unittest import skipIf
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.models import LicenseRequest
from tests.test_helpers import (
    BaseSeleniumTestCase,
    getExamplePath,
    SELENIUM_AVAILABLE,
)


class XMLUploadTestCase(TestCase):

    def test_xml_upload(self):
        """GET Request for XML upload page"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("xml-upload"),follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)

        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.get(reverse("xml-upload"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/xml_upload.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"xml_upload")
        self.client.logout()

    def test_xml_file_upload_post_without_login(self):
        """POST Request for XML file upload without login or ANONYMOUS_LOGIN_DISABLED """
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            self.xml_file = open(getExamplePath("Adobe-Glyph.xml"))
            resp = self.client.post(reverse("xml-upload"),{'file': self.xml_file, 'uploadButton': 'uploadButton', 'page_id': 'asfw2432'},follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.xml_file.close()
            self.assertEqual(resp.status_code,200)

    def test_xml_file_upload_post_without_file(self):
        """POST Request for XML file upload without any file"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'uploadButton': 'uploadButton', 'page_id': 'afaw214a'},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        resp = self.client.post(reverse("xml-upload"),{'uploadButton': 'uploadButton', 'page_id': 'afaw214a',"file": ""},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.client.logout()

    def test_xml_file_upload(self):
        """POST request for XML file upload"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        self.xml_file = open(getExamplePath("Adobe-Glyph.xml"))
        resp = self.client.post(reverse("xml-upload"),{'file': self.xml_file, 'uploadButton': 'uploadButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.xml_file.close()
        self.client.logout()

    def test_invalid_file_upload(self):
        """ POST request for uploading non XML file"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
        resp = self.client.post(reverse("xml-upload"),{'file': self.tv_file, 'uploadButton': 'uploadButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.tv_file.close()
        self.client.logout()

    def test_xml_input_textarea(self):
        """ POST request for xml input using textarea"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        self.xml_text = "<spdx></spdx>"
        resp = self.client.post(reverse("xml-upload"),{'xmltext': self.xml_text, 'xmlTextButton': 'xmlTextButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()

    def test_xml_blank_input_textarea(self):
        """ POST request for blank xml input using textarea"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        self.xml_text = ""
        resp = self.client.post(reverse("xml-upload"),{'xmltext': self.xml_text, 'xmlTextButton': 'xmlTextButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.client.logout()

    def test_license_name(self):
        """POST request for xml input using license identifier or full name"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'licenseName': 'Apache-2.0', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        resp = self.client.post(reverse("xml-upload"),{'licenseName': 'Apache License 2.0', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()

    def test_exception_name(self):
        """POST request for xml input using exception identifier or full name"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'licenseName': '389-exception', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        resp = self.client.post(reverse("xml-upload"),{'licenseName': '389 Directory Server Exception', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()

    def test_invalid_license_name(self):
        """ POST request for xml input using invalid license name"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'licenseName': 'sampleTestLicense', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.client.logout()

    def test_blank_license_name(self):
        """ POST request for xml input using invalid license name"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'licenseName': '', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.client.logout()

    def test_xml_new_file(self):
        """ POST request for making new XML license"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'newButton': 'newButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()


class ValidateXMLViewsTestCase(TestCase):

    def test_validate_xml(self):
        """GET Request for validate_xml"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("validate-xml"),follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)

        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        resp2 = self.client.get(reverse("validate-xml"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertNotEqual(resp2.redirect_chain,[])
        self.assertIn(settings.HOME_URL, (i[0] for i in resp2.redirect_chain))
        self.assertEqual(resp2.resolver_match.func.__name__,"index")
        self.client.logout()

    def test_validate_xml_post_without_login(self):
        """POST Request for validate xml without login or ANONYMOUS_LOGIN_DISABLED """
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            self.xml_text = open(getExamplePath("Adobe-Glyph.xml")).read()
            resp = self.client.post(reverse("validate-xml"),{'xmlText' : self.xml_text},follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)

    def test_validate_xml_post_without_xmlText(self):
        """POST Request for validate xml without any xml text"""
        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        resp = self.client.post(reverse("validate-xml"),{},follow=True,secure=True)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"No XML text given.")
        self.assertEqual(resp.redirect_chain,[])
        self.client.logout()

    def test_valid_xml(self):
        """POST Request for validating a valid XML text """
        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        self.xml_text = open(getExamplePath("Adobe-Glyph.xml")).read()
        resp = self.client.post(reverse("validate-xml"),{'xmlText': self.xml_text},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content, b"This XML is valid against SPDX License Schema.")
        self.client.logout()

    def test_invalid_xml(self):
        """POST Request for validating an invalid XML text """
        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        self.xml_text = open(getExamplePath("invalid_license.xml")).read()
        resp = self.client.post(reverse("validate-xml"),{'xmlText' : self.xml_text},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()


# @skipIf is intentionally kept alongside the BaseSeleniumTestCase.setUp check to skip
# the class before any fixtures are set up, which is faster.
@tag("selenium")
@skipIf(not SELENIUM_AVAILABLE, "Selenium not available (Firefox or Chrome required)")
class LicenseXMLEditorTestCase(BaseSeleniumTestCase):

    def setUp(self):
        super(LicenseXMLEditorTestCase, self).setUp()
        self.initialXML = '<?xml version="1.0" encoding="UTF-8"?>\n<SPDXLicenseCollection xmlns="http://www.spdx.org/license">\n   <license>\n   </license>\n</SPDXLicenseCollection>'
        self.invalidXML = '<?xml version="1.0" encoding="UTF-8"?><SPDXLicenseCollection xmlns="http://www.spdx.org/license"><license></license>'

    def test_tree_editor_attributes(self):
        """ Test for adding, editing and deleting attributes using tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element(By.LINK_TEXT, 'New license XML').click()
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "new-button"))
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        self.disable_animations()
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTreeEditor")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#tree.active"))
        )
        """ Adding attribute """
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[2]/div/ul/li/ul/li[3]/img[3]"))).click()
        driver.find_element(By.CLASS_NAME, "newAttributeName").send_keys("firstAttribute")
        driver.find_element(By.CLASS_NAME, "newAttributeValue").send_keys("firstValue")
        driver.find_element(By.CLASS_NAME, "addNewAttribute").click()
        """ Adding Invalid attribute """
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[2]/div/ul/li/ul/li[3]/img[3]"))).click()
        driver.find_element(By.CLASS_NAME, "newAttributeName").send_keys("secondAttribute")
        driver.find_element(By.CLASS_NAME, "addNewAttribute").click()
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "modal-body")))
        modal_text = driver.find_element(By.ID, "modal-body").text
        self.assertEqual(modal_text, "Please enter valid attribute name and value")
        driver.find_element(By.CSS_SELECTOR, "div.modal-footer button.btn").click()
        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "myModal")))
        driver.find_element(By.CLASS_NAME, "newAttributeValue").send_keys("secondValue")
        driver.find_element(By.CLASS_NAME, "cancel").click()
        """ Editing attribute """
        driver.find_elements(By.CSS_SELECTOR, "span.attributeValue")[1].click()
        driver.find_element(By.CSS_SELECTOR, "input.textbox").clear()
        driver.find_element(By.CSS_SELECTOR, "input.textbox").send_keys("Edited Value")
        driver.find_element(By.CSS_SELECTOR, "img.editAttribute").click()
        WebDriverWait(driver, 30).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "span.attributeValue")[1].text == "Edited Value"
        )
        editedValue = driver.find_elements(By.CSS_SELECTOR, "span.attributeValue")[1].text
        self.assertEqual(editedValue, "Edited Value")
        """ Delete attribute """
        driver.find_elements(By.CSS_SELECTOR, "span.attributeValue")[1].click()
        driver.find_element(By.CSS_SELECTOR, "img.removeAttribute").click()
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "modal-body")))
        modal_text = driver.find_element(By.ID, "modal-body").text
        self.assertEqual(modal_text, "Are you sure you want to delete this attribute? This action cannot be undone.")
        driver.find_element(By.ID, "modalOk").click()
        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "myModal")))
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTextEditor")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#text.active"))
        )
        finalXML = driver.execute_script("return editor.getValue().trim()")
        self.assertEqual(self.initialXML, finalXML)

    def test_split_tree_editor_attributes(self):
        """ Test for adding, editing and deleting attributes using split view tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to split view """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element(By.LINK_TEXT, 'New license XML').click()
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "new-button"))
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        self.disable_animations()
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabSplitView")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#split.active"))
        )
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#splitTreeView li.addChild"))
        )
        """ Adding attribute """
        driver.execute_script("document.getElementsByClassName('addAttribute')[1].click()")
        driver.execute_script("document.getElementsByClassName('newAttributeName')[0].value = 'firstAttribute'")
        driver.execute_script("document.getElementsByClassName('newAttributeValue')[0].value = 'firstValue'")
        driver.execute_script("document.getElementsByClassName('addNewAttribute')[0].click()")
        WebDriverWait(driver, 30).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#splitTreeView span.attributeValue")) > 1
        )
        """ Adding Invalid attribute """
        driver.execute_script("document.getElementsByClassName('addAttribute')[1].click()")
        driver.execute_script("document.getElementsByClassName('newAttributeName')[0].value = 'secondAttribute'")
        driver.execute_script("document.getElementsByClassName('addNewAttribute')[0].click()")
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "modal-body")))
        modal_text = driver.find_element(By.ID, "modal-body").text
        self.assertEqual(modal_text, "Please enter valid attribute name and value")
        driver.execute_script("document.querySelector('div.modal-footer button.btn').click()")
        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "myModal")))
        driver.execute_script("document.getElementsByClassName('newAttributeValue')[0].value = 'secondValue'")
        driver.execute_script("document.getElementsByClassName('cancel')[0].click()")
        """ Editing attribute """
        driver.execute_script("document.querySelectorAll('span.attributeValue')[1].click()")
        driver.execute_script("document.querySelector('input.textbox').value = ''")
        driver.execute_script("document.querySelector('input.textbox').value = 'Edited Value'")
        driver.execute_script("document.querySelector('img.editAttribute').click()")
        WebDriverWait(driver, 30).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "span.attributeValue")[1].text == "Edited Value"
        )
        editedValue = driver.find_elements(By.CSS_SELECTOR, "span.attributeValue")[1].text
        self.assertEqual(editedValue, "Edited Value")
        """ Delete attribute """
        driver.execute_script("document.querySelectorAll('span.attributeValue')[1].click()")
        driver.execute_script("document.querySelector('img.removeAttribute').click()")
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "modal-body")))
        modal_text = driver.find_element(By.ID, "modal-body").text
        self.assertEqual(modal_text, "Are you sure you want to delete this attribute? This action cannot be undone.")
        driver.execute_script("document.getElementById('modalOk').click()")
        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "myModal")))
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTextEditor")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#text.active"))
        )
        finalXML = driver.execute_script("return editor.getValue().trim()")
        self.assertEqual(self.initialXML, finalXML)

    def test_tree_editor_nodes(self):
        """ Test for adding and deleting nodes(tags) using tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element(By.LINK_TEXT, 'New license XML').click()
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "new-button"))
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        self.disable_animations()
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTreeEditor")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#tree.active"))
        )
        """ Adding node """
        driver.find_element(By.CSS_SELECTOR, "li.addChild.last").click()
        driver.find_element(By.CSS_SELECTOR, "input.textbox").send_keys("newNode")
        driver.find_element(By.CLASS_NAME, "buttonAddChild").click()
        """ Adding invalid node """
        driver.find_element(By.CSS_SELECTOR, "li.addChild.last").click()
        driver.find_element(By.CLASS_NAME, "buttonAddChild").click()
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "modal-body")))
        modal_text = driver.find_element(By.ID, "modal-body").text
        self.assertEqual(modal_text, "The tag name cannot be empty. Please enter a valid tag name.")
        driver.find_element(By.CSS_SELECTOR, "div.modal-footer button.btn").click()
        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "myModal")))
        driver.find_element(By.CLASS_NAME, "cancelAddChild").click()
        """ Delete attribute """
        driver.find_elements(By.CSS_SELECTOR, "img.deleteNode")[2].click()
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "modal-body")))
        modal_text = driver.find_element(By.ID, "modal-body").text
        self.assertEqual(modal_text, "Are you sure you want to delete this tag? This cannot be undone.")
        driver.find_element(By.ID, "modalOk").click()
        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "myModal")))
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTextEditor")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#text.active"))
        )
        finalXML = driver.execute_script("return editor.getValue().trim()")
        self.assertEqual(self.initialXML, finalXML)

    def test_split_tree_editor_nodes(self):
        """ Test for adding and deleting nodes(tags) using split view tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to split view """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element(By.LINK_TEXT, 'New license XML').click()
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "new-button"))
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        self.disable_animations()
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabSplitView")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#split.active"))
        )
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#splitTreeView li.addChild"))
        )
        """ Adding node """
        driver.execute_script("document.querySelectorAll('li.addChild.last')[1].click()")
        driver.execute_script("document.querySelector('input.textbox').value = 'newNode'")
        driver.execute_script("document.getElementsByClassName('buttonAddChild')[0].click()")
        """ Adding invalid node """
        driver.execute_script("document.querySelectorAll('li.addChild.last')[1].click()")
        driver.execute_script("document.getElementsByClassName('buttonAddChild')[0].click()")
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "modal-body")))
        modal_text = driver.find_element(By.ID, "modal-body").text
        self.assertEqual(modal_text, "The tag name cannot be empty. Please enter a valid tag name.")
        driver.execute_script("document.querySelector('div.modal-footer button.btn').click()")
        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "myModal")))
        driver.execute_script("document.getElementsByClassName('cancelAddChild')[0].click()")
        """ Delete attribute """
        driver.execute_script("document.querySelectorAll('img.deleteNode')[2].click()")
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "modal-body")))
        modal_text = driver.find_element(By.ID, "modal-body").text
        self.assertEqual(modal_text, "Are you sure you want to delete this tag? This cannot be undone.")
        driver.execute_script("document.getElementById('modalOk').click()")
        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "myModal")))
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTextEditor")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#text.active"))
        )
        finalXML = driver.execute_script("return editor.getValue().trim()")
        self.assertEqual(self.initialXML, finalXML)

    def test_tree_editor_text(self):
        """ Test for adding, editing and deleting text inside tags using tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element(By.LINK_TEXT, 'New license XML').click()
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "new-button"))
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        self.disable_animations()
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTreeEditor")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#tree.active"))
        )
        """ Adding text """
        try:
            empty_text_li = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.emptyText"))
            )
            empty_text_li.click()
        except Exception as e:
            try:
                print("BROWSER CONSOLE LOGS:", driver.get_log('browser'))
            except Exception:
                pass
            print("PAGE SOURCE ON FAILURE:", driver.page_source)
            raise e
        driver.find_element(By.CSS_SELECTOR, "div.treeContainer textarea").send_keys("This is some sample text.")
        driver.find_element(By.CLASS_NAME, "editNodeText").click()
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "li.nodeText"), "This is some sample text.")
        )
        nodeText = driver.find_element(By.CSS_SELECTOR, "li.nodeText").text
        self.assertEqual(nodeText, "This is some sample text.")
        """ Editing text """
        driver.find_element(By.CSS_SELECTOR, "li.nodeText").click()
        driver.find_element(By.CSS_SELECTOR, "div.treeContainer textarea").clear()
        driver.find_element(By.CSS_SELECTOR, "div.treeContainer textarea").send_keys("Edited text.")
        driver.find_element(By.CLASS_NAME, "editNodeText").click()
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "li.nodeText"), "Edited text.")
        )
        nodeText = driver.find_element(By.CSS_SELECTOR, "li.nodeText").text
        self.assertEqual(nodeText, "Edited text.")
        """ Delete text """
        driver.find_element(By.CSS_SELECTOR, "li.nodeText").click()
        driver.find_element(By.CSS_SELECTOR, "div.treeContainer textarea").clear()
        driver.find_element(By.CLASS_NAME, "editNodeText").click()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.emptyText"))
        )
        nodeText = driver.find_element(By.CSS_SELECTOR, "li.emptyText").text
        self.assertEqual(nodeText, "(No text value. Click to edit.)")
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTextEditor")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#text.active"))
        )
        finalXML = driver.execute_script("return editor.getValue().trim()")
        self.assertEqual(self.initialXML, finalXML)

    def test_split_tree_editor_text(self):
        """ Test for adding, editing and deleting text inside tags using split view tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to split view """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element(By.LINK_TEXT, 'New license XML').click()
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "new-button"))
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        self.disable_animations()
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabSplitView")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#split.active"))
        )
        time.sleep(0.5)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#splitTreeView li.addChild"))
        )
        """ Adding text """
        # Blur the text editor first to ensure all blur/update events are fired and processed
        driver.execute_script("if (typeof splitTextEditor !== 'undefined' && splitTextEditor.getInputField) { splitTextEditor.getInputField().blur(); } document.activeElement.blur();")
        time.sleep(0.3)
        
        split_empty_texts = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "#splitTreeView li.emptyText")
        )
        el_to_click = split_empty_texts[1]
        el_to_click.click()
        
        textarea = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#splitTreeView textarea"))
        )
        textarea.send_keys("This is some sample text.")
        driver.find_element(By.CSS_SELECTOR, "#splitTreeView button.editNodeText").click()
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#splitTreeView li li li.nodeText"), "This is some sample text.")
        )
        nodeText = driver.find_element(By.CSS_SELECTOR, "#splitTreeView li li li.nodeText").text
        self.assertEqual(nodeText, "This is some sample text.")
        """ Editing text """
        driver.find_element(By.CSS_SELECTOR, "#splitTreeView li li li.nodeText").click()
        textarea = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#splitTreeView textarea"))
        )
        textarea.clear()
        textarea.send_keys("Edited text.")
        driver.find_element(By.CSS_SELECTOR, "#splitTreeView button.editNodeText").click()
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#splitTreeView li li li.nodeText"), "Edited text.")
        )
        nodeText = driver.find_element(By.CSS_SELECTOR, "#splitTreeView li li li.nodeText").text
        self.assertEqual(nodeText, "Edited text.")
        """ Delete text """
        driver.find_element(By.CSS_SELECTOR, "#splitTreeView li li li.nodeText").click()
        textarea = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#splitTreeView textarea"))
        )
        textarea.clear()
        driver.find_element(By.CSS_SELECTOR, "#splitTreeView button.editNodeText").click()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#splitTreeView li li li.emptyText"))
        )
        nodeText = driver.find_element(By.CSS_SELECTOR, "#splitTreeView li li li.emptyText").text
        self.assertEqual(nodeText, "(No text value. Click to edit.)")
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTextEditor")))
        driver.execute_script("arguments[0].click();", tab)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#text.active"))
        )
        finalXML = driver.execute_script("return editor.getValue().trim()")
        self.assertEqual(self.initialXML, finalXML)

    def test_tree_editor_invalid_xml(self):
        """ Test for invalid XML text provided """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element(By.ID, "xmltext").send_keys(self.invalidXML)
        driver.find_element(By.ID, "xmlTextButton").click()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        self.disable_animations()
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabTreeEditor")))
        driver.execute_script("arguments[0].click();", tab)
        """ Checking for error message """
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h2.xmlParsingErrorMessage"))
        )
        error_title = driver.find_element(By.CSS_SELECTOR, "h2.xmlParsingErrorMessage").text
        error_message = driver.find_element(By.CSS_SELECTOR, "span.xmlParsingErrorMessage").text
        self.assertEqual(error_title, "Invalid XML.")
        assert "xml" in error_message.lower() and "error" in error_message.lower()

    def test_split_tree_editor_invalid_xml(self):
        """ Test for invalid XML text provided """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element(By.ID, "xmltext").send_keys(self.invalidXML)
        driver.find_element(By.ID, "xmlTextButton").click()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        self.disable_animations()
        tab = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabSplitView")))
        driver.execute_script("arguments[0].click();", tab)
        """ Checking for error message """
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h2.xmlParsingErrorMessage"))
        )
        error_title = driver.find_element(By.CSS_SELECTOR, "h2.xmlParsingErrorMessage").text
        error_message = driver.find_element(By.CSS_SELECTOR, "span.xmlParsingErrorMessage").text
        self.assertEqual(error_title, "Invalid XML.")
        assert "xml" in error_message.lower() and "error" in error_message.lower()


class EditLicenseXmlViewsTestCase(TestCase):
    def test_edit_license_xml(self):
        """View for editing the xml of a license, given its id"""
        license_obj = LicenseRequest.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        license_id = license_obj.id
        resp = self.client.get(reverse("license_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/editor.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_xml")

    def test_error_license_requests_edit_xml(self):
        """Check if error page is displayed when the license id does not exist"""
        license_id = 0
        resp = self.client.get(reverse("license_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_xml")

    def test_no_license_id_on_license_requests_edit_xml(self):
        """Check if the redirect works if no license id is provided in the url"""
        resp = self.client.get(reverse("license_xml_editor_none"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn("app/license_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseRequests")
