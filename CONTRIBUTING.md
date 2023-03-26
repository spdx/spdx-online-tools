# Contributing to SPDX Online Tools

Thank you for considering contributing to SPDX Online Tools! This document will provide you with information about how to contribute to this project.

# Before you contribute to the SPDX Online Tools

Please familiarize yourself with the SPDX Online Tools and its supporting documentation, so that you understand the pertinent context around the list itself:

- [Working of the Tool](https://github.com/spdx/spdx-online-tools/wiki/Online-SPDX-Tool,-Google-Summer-of-Code-2017)

- [SPDX License List Matching Guidelines](https://spdx.org/spdx-license-list/matching-guidelines) provides guidelines to be used for the purposes of matching licenses and license exceptions against those included on the SPDX License List.

- [SPDX Specification](https://spdx.org/specifications): It is helpful to be familiar with certain sections of the SPDX Specification that use or deal with the SPDX License List. In particular: sub-sections related to license information in Section 3, 4, and 6; Appendices II, IV, and V.

# Join the mailing list and our bi-weekly calls

The SPDX License List is maintained by the SPDX Legal Team. Work and discussion is primarily done via:

- **join the mailing list**: Please introduce yourself and let us know a bit about your interest in SPDX! The mailing list is our traditional form of communication. Join the mailing list, see archive, and manage your subscription at [lists.spdx.org](https://lists.spdx.org/g/Spdx-legal).
- **join the bi-weekly calls**: Bi-weekly conference call info is sent prior to the calls via the mailing list. If you join the mailing list, you should get a recurring invite at the beginning of each calendar year. Meeting minutes for the calls are in the [SPDX meetings repo](https://github.com/spdx/meetings/tree/main/legal); historical meeting minutes can be found at http://wiki.spdx.org/

# Working of the tool

It works exactly how the java tools works except it takes minimum input from the user and do the rest from those input. There are 4 tools in the online tool :

1. _Validation_ - To verify and validate valid SPDX tag/value file and rdf file.
2. _Conversion_ - To convert from one SPDX format to another.
3. _Comparison_ - To compare multiple SPDX RDF file and return the result as an excel sheet.
4. _Check License_ – To compares license text to the SPDX listed licenses

**Validation:**
The user inputs a file and upload it to the server. Then the Django app through JPype calls the java tool jar file and run the verify function and return the result as Success or Error. Success shows that the file is valid as per the latest SPDX specifications. Error shows that the file is either an invalid file format or an invalid Tag/value or RDF file. If it’s the later one, it shows the line no. of the error or the XML tag that file have missed.

**Comparison:**
This tool has 2 types of file input method. The user can select the file one by one if the files are in different folder or select them all at once if they are all in the same folder.
After the files are uploaded, they are first verified whether they are valid or not. If they are not valid, the user is shown which file is invalid and what errors are there.
If all the files are valid (or only warnings are raised) then the comparison method is called and the files are compared and an excel file is available for the user to download.

**Convert:**
The user can convert from one SPDX file format to another like Tag value file to RDF or vice versa. RDF to excel or vice versa.
The tool first validates the file whether it is valid or not, and then only call the convert function and return the downloadable file.

**Check License:**
The user can compares license text to the SPDX listed licenses . The user inputs the license text to be searched and the tool searches the text in the license list from [spdx.org/licenses](https://spdx.org/licenses/).

# Working of the REST API

The API works the same way as the above tools. You can find about the file input fields for the different tools [[here | REST-API-Fields-Request-and-Response]]

# Getting started

Below are some ways you can get started participating and contributing!

- Make suggestions to improvement for documentation: Newcomers have a great perspective as to the effectiveness of documentation! You can make suggestions via an issue, if you want to discuss the changes or if there is something specific that could be updated, then create a PR

- Review PRs

- Solving issues with the tag [good-first-issue](https://github.com/spdx/spdx-online-tools/labels/good-first-issue) can be a great starting point for all the new developers
