# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

import datetime
import os
import shutil
from unittest import skip, skipIf
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from social_django.models import UserSocialAuth

from app.generateXml import generateLicenseXml
from app.models import LicenseNamespace, LicenseRequest
from app.scripts.cleanup import clean_media
from src.secret import getAccessToken, getGithubUserId, getGithubUserName
from tests.test_helpers import BaseSeleniumTestCase, SELENIUM_AVAILABLE, getExamplePath


class TestUtil(TestCase):
    def gitHubLogin(self):
        TEST_LOGIN_INFO = {
            "provider": "github",
            "uid": str(getGithubUserId()),
            "access_token": getAccessToken(),
            "login": getGithubUserName(),
            "id": getGithubUserId(),
            "password": "pass",
        }
        self.user = User.objects.create(username=TEST_LOGIN_INFO["login"],
                                        is_active=True,
                                        is_superuser=True)
        self.user.set_password(TEST_LOGIN_INFO["password"])
        self.user.save()
        UserSocialAuth.objects.create(provider=TEST_LOGIN_INFO["provider"],
                                      uid=TEST_LOGIN_INFO["uid"],
                                      extra_data=TEST_LOGIN_INFO,
                                      user=self.user)
        self.user = authenticate(username=TEST_LOGIN_INFO["login"],
                                 password=TEST_LOGIN_INFO["password"])
        login = self.client.login(username=TEST_LOGIN_INFO["login"],
                                  password=TEST_LOGIN_INFO["password"])
        return login





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
        import time
        time.sleep(0.5)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#splitTreeView li.addChild"))
        )
        """ Adding text """
        import time
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
        print("DEBUG INVALID XML ERROR TITLE:", error_title)
        print("DEBUG INVALID XML ERROR MESSAGE:", error_message)
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
        print("DEBUG SPLIT INVALID XML ERROR TITLE:", error_title)
        print("DEBUG SPLIT INVALID XML ERROR MESSAGE:", error_message)
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


@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class LicenseNamespaceViewsTestCase(TestCase):

    def test_license_requests(self):
        """GET Request for license requests list"""
        resp = self.client.get(reverse("license-namespace-requests"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/license_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceRequests")


# @skipIf is intentionally kept alongside the BaseSeleniumTestCase.setUp check to skip
# the class before any fixtures are set up, which is faster.
@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
@skipIf(not SELENIUM_AVAILABLE, "Selenium not available (Firefox or Chrome required)")
class PromoteLicenseNamespaceViewsTestCase(BaseSeleniumTestCase):

    def setUp(self):
        super(PromoteLicenseNamespaceViewsTestCase, self).setUp()
        login = TestUtil.gitHubLogin(self)
        self.assertTrue(login)


    @skipIf(not getAccessToken() or not getGithubUserId() or not getGithubUserName(), "You need to set GitHub parameters in the secret.py file for this test to be executed properly.")
    def test_promote_license_namespace_feature(self):
        """Check if the license namespace is promoted when the promote action is taken"""
        # GitHub access token,id and username should be added in .env to execute the test properly
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_namespace_requests/')
        table_contents = driver.find_element(By.CSS_SELECTOR, 'tbody').text
        self.assertEqual(table_contents, "No data available in table")
        xml = generateLicenseXml('', "0BSD", "BSD Zero Clause License-00",
            '', ["http://wwww.spdx.org"], '', '', '')
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                      licenseAuthorName="John Doe",
                                                      shortIdentifier="0BSD",
                                                      archive="False",
                                                      promoted="False",
                                                      url="http://wwww.spdx.org",
                                                      description="Description",
                                                      notes="Notes",
                                                      namespace="bsd-zero-clause-license-00",
                                                      userEmail="johndoe@gmail.com",
                                                      publiclyShared="True",
                                                      license_list_url="http://wwww.spdx.org",
                                                      github_repo_url="http://wwww.spdx.org",
                                                      xml=xml)
        driver.refresh()
        license_name = driver.find_element(By.CSS_SELECTOR, 'td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).promoted, False)

        resp = self.client.post(reverse("promoted-license-namespace-xml"),
                                {"promoted": True, "license_id": license_obj.id},
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])


@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class ArchiveLicenseNamespaceViewsTestCase(TestCase):

    def test_archive_license_requests(self):
        """GET Request for archive license namespace requests list"""
        resp = self.client.get(reverse("archive-license-namespace-xml"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/archive_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"archiveNamespaceRequests")

    def test_error_archive_license_namespace(self):
        """Check if error page is displayed when the license id does not exist for archive license namespace"""
        license_id = 0
        resp = self.client.get(reverse("archived-license-namespace-information", args=(license_id,)),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceInformation")


# @skipIf is intentionally kept alongside the BaseSeleniumTestCase.setUp check to skip
# the class before any fixtures are set up, which is faster.
@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
@skipIf(not SELENIUM_AVAILABLE, "Selenium not available (Firefox or Chrome required)")
class ArchiveLicenseNamespaceSeleniumTestCase(BaseSeleniumTestCase):

    def test_archive_license_namespace_feature(self):
        """Check if the license namespace is shifted to archive namespace when archive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_namespace_requests/')
        table_contents = driver.find_element(By.CSS_SELECTOR, 'tbody').text
        self.assertEqual(table_contents, "No data available in table")
        xml = generateLicenseXml('', "0BSD", "BSD Zero Clause License-00",
            '', "http://wwww.spdx.org", '', '', '')
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                      licenseAuthorName="John Doe",
                                                      shortIdentifier="0BSD",
                                                      archive="False",
                                                      url="http://wwww.spdx.org",
                                                      description="Description",
                                                      notes="Notes",
                                                      namespace="bsd-zero-clause-license-00",
                                                      userEmail="johndoe@gmail.com",
                                                      publiclyShared="True",
                                                      license_list_url="http://wwww.spdx.org",
                                                      github_repo_url="http://wwww.spdx.org",
                                                      xml=xml)
        driver.refresh()
        license_name = driver.find_element(By.CSS_SELECTOR, 'td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).archive, False)
        driver.find_element(By.ID, 'archive_button' + str(license_obj.id)).click()
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'confirm_archive')))
        driver.find_element(By.ID, 'confirm_archive').click()
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'tbody'), "No data available in table")
        )
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).archive, True)

    def test_unarchive_license_namespace_feature(self):
        """Check if license namespace is shifted back to license namespace when unarchive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/archive_namespace_requests/')
        table_contents = driver.find_element(By.CSS_SELECTOR, 'tbody').text
        self.assertEqual(table_contents, "No data available in table")
        archive_license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                              licenseAuthorName="John Doe",
                                                              shortIdentifier="0BSD",
                                                              archive="True",
                                                              url="http://wwww.spdx.org",
                                                              description="Description",
                                                              notes="Notes",
                                                              namespace="bsd-zero-clause-license-00",
                                                              userEmail="johndoe@gmail.com",
                                                              publiclyShared="True",
                                                              license_list_url="http://wwww.spdx.org",
                                                              github_repo_url="http://wwww.spdx.org")
        driver.refresh()
        license_name = driver.find_element(By.CSS_SELECTOR, 'td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=archive_license_obj.id).archive, True)
        driver.find_element(By.ID, 'unarchive_button' + str(archive_license_obj.id)).click()
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'confirm_unarchive')))
        driver.find_element(By.ID, 'confirm_unarchive').click()
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'tbody'), "No data available in table")
        )
        self.assertEqual(LicenseNamespace.objects.get(id=archive_license_obj.id).archive, False)


@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class SubmitNewLicenseNamespaceViewsTestCase(TestCase):

    def initialise(self):
        self.fullname = "BSD Zero Clause License"
        self.shortIdentifier = "0BSD"
        self.sourceUrl = "http://landley.net/toybox/license.html"
        self.license_list_url = self.sourceUrl
        self.github_repo_url = self.sourceUrl
        self.osiApproved = "Unknown"
        self.comments = ""
        self.notes = ""
        self.licenseHeader = ""
        self.text ='<text> <copyrightText> <p>Copyright (C) 2006 by Rob Landley &lt;rob@landley.net&gt;</p> </copyrightText> <p>Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.</p> <p>THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.</p> </text>'
        self.userEmail = "test@mail.com"
        self.licenseAuthorName = "John Doe"
        self.listVersionAdded = ""
        self.namespace = "j-d-ns"
        self.xml = '<SPDXLicenseCollection xmlns="http://www.spdx.org/license"> <license isOsiApproved="false" licenseId="0BSD" listVersionAdded="" name="BSD Zero Clause License"> <crossRefs> <crossRef> http://landley.net/toybox/license.html</crossRef> </crossRefs> <standardLicenseHeader /> <notes /> <text> <p> &lt;text&gt; &lt;copyrightText&gt; &lt;p&gt;Copyright (C) 2006 by Rob Landley &amp;lt;rob@landley.net&amp;gt;&lt;/p&gt; &lt;/copyrightText&gt; &lt;p&gt;Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.&lt;/p&gt; &lt;p&gt;THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.&lt;/p&gt; &lt;/text&gt;</p> </text> </license> </SPDXLicenseCollection> '
        self.data_no_author = {"fullname": self.fullname, "shortIdentifier": self.shortIdentifier,
                    "url": self.sourceUrl,'osiApproved': self.osiApproved, 'notes': self.notes,
                    "licenseHeader": self.licenseHeader, "text": self.text, "userEmail": self.userEmail,
                    "urlType": "tests", "namespace": self.namespace, "license_list_url": self.license_list_url,
                    "github_repo_url": self.github_repo_url, "licenseAuthorName": self.licenseAuthorName}

    @skip("URL disabled: license namespace not accepted into SPDX spec (see issue #337)")
    def test_submit_new_license_namespace(self):
        """GET Request for submit a new license namespace.

        Note that the license namespace feature is not accepted into the SPDX
        specification, and therefore this URL is disabled.
        The test is skipped to avoid failures.

        See more details in the following links:
        - https://github.com/spdx/spdx-spec/issues/113
        - https://github.com/spdx/spdx-spec/pull/209
        - https://github.com/spdx/spdx-online-tools/issues/337#issuecomment-1504244538
        """
        resp = self.client.get(reverse("submit-new-license-namespace"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/submit_new_license_namespace.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"submitNewLicenseNamespace")
        self.assertIn("form",resp.context)
        self.assertIn("fullname",resp.context["form"].fields)
        self.assertIn("organisation",resp.context["form"].fields)
        self.assertIn("namespace",resp.context["form"].fields)
        self.assertIn("shortIdentifier",resp.context["form"].fields)
        self.assertIn("publiclyShared",resp.context["form"].fields)
        self.assertIn("url",resp.context["form"].fields)
        self.assertIn("license_list_url",resp.context["form"].fields)
        self.assertIn("github_repo_url",resp.context["form"].fields)
        self.assertIn("description",resp.context["form"].fields)
        self.assertIn("licenseAuthorName",resp.context["form"].fields)
        self.assertIn("userEmail",resp.context["form"].fields)

    def test_generate_xml(self):
        """View for generating an xml from license namespace submittal form fields"""
        self.initialise()
        xml = generateLicenseXml(self.osiApproved, self.shortIdentifier, self.fullname, self.listVersionAdded,
                                [self.sourceUrl], self.licenseHeader, self.notes, self.text).replace(">","> ")
        self.assertEqual(self.xml, xml)

    @skip("URL disabled: license namespace not accepted into SPDX spec (see issue #337)")
    @skipIf(not getAccessToken() or not getGithubUserId() or not getGithubUserName(), "You need to set GitHub parameters in the secret.py file for this test to be executed properly.")
    def test_post_submit(self):
        """POST Request for submit a new license namespace.

        Note that the license namespace feature is not accepted into the SPDX
        specification, and therefore this URL is disabled.
        The test is skipped to avoid failures.

        See more details in the following links:
        - https://github.com/spdx/spdx-spec/issues/113
        - https://github.com/spdx/spdx-spec/pull/209
        - https://github.com/spdx/spdx-online-tools/issues/337#issuecomment-1504244538
        """
        login = TestUtil.gitHubLogin(self)
        self.assertTrue(login)
        self.initialise()
        resp = self.client.post(reverse("submit-new-license-namespace"),
                                self.data_no_author,
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])


@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class EditLicenseNamespaceXmlViewsTestCase(TestCase):
    def test_edit_license_xml(self):
        """View for editing the xml of a license namespace, given its id"""
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        license_id = license_obj.id
        resp = self.client.get(reverse("license_namespace_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/ns_editor.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_namespace_xml")

    def test_error_license_requests_edit_xml(self):
        """Check if error page is displayed when the license namespace id does not exist"""
        license_id = 0
        resp = self.client.get(reverse("license_namespace_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_namespace_xml")

    def test_no_license_id_on_license_requests_edit_xml(self):
        """Check if the redirect works if no license namespace id is provided in the url"""
        resp = self.client.get(reverse("license_namespace_xml_editor_none"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn("app/license_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceRequests")


class TestCronJob(TestCase):
    def test_clean_media_deletes_only_expired_files(self):
        """Check if the files older than 10 days are getting deleted"""
        test_dir = os.path.join(settings.MEDIA_ROOT, "AnonymousUser")
        os.makedirs(test_dir, exist_ok=True)
        self.addCleanup(shutil.rmtree, test_dir, True)
        for i in range(1, 11):
            file_path = os.path.join(test_dir, f"test_file_{i}.txt")
            with open(file_path, "w") as f:
                f.write("test")
            # set file creation time to 11 days ago
            if i <= 5:
                creation_time = datetime.datetime.now() - datetime.timedelta(days=11)
                os.utime(
                    file_path, (creation_time.timestamp(), creation_time.timestamp())
                )

        # check that only files older than 10 days were deleted
        deleted_files = clean_media()

        self.assertEqual(
            [file_info["name"] for file_info in deleted_files],
            [f"test_file_{i}.txt" for i in range(1, 6)],
        )
        for file_info in deleted_files:
            self.assertIn("modified_at", file_info)

        for i in range(1, 11):
            file_path = os.path.join(test_dir, f"test_file_{i}.txt")
            if i <= 5:
                self.assertFalse(
                    os.path.exists(file_path), f"{file_path} should have been deleted"
                )
            else:
                self.assertTrue(
                    os.path.exists(file_path),
                    f"{file_path} should not have been deleted",
                )

    def test_cleanup_management_command(self):
        """cleanup_media command delegates with correct threshold values"""
        with patch(
            "app.management.commands.cleanup_media.clean_media", return_value=[]
        ) as clean_media_mock:
            call_command("cleanup_media")
            call_command("cleanup_media", "--days-threshold", "30")

        self.assertEqual(clean_media_mock.call_count, 2)
        clean_media_mock.assert_any_call(days_threshold=10)
        clean_media_mock.assert_any_call(days_threshold=30)
