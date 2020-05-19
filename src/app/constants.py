from django.utils.safestring import mark_safe

# License submission form help text

FULL_NAME_HELP_TEXT = mark_safe('\u2022 The full name may omit certain word, such as \'the,\' for alphabetical sorting purposes. <br/>'
                          '\u2022 No commas in full name of license or exception. <br/>'
                          '\u2022 The word \'version\' is not spelled out; \'v\' or nothing is used to indicate license version (for space reasons) <br/>'
                          '\u2022 For version, use lower case v and no period or space between v and the number. <br/>'
                          '\u2022 No abbreviations are included (in parenthesis) after the full name.')

SHORT_IDENTIFIER_HELP_TEXT = mark_safe('\u2022 Short identifier to be used to identify a license or exception match to licenses or exceptions in the context of an SPDX file, a source file, or elsewhere. <br/>'
                                        '\u2022 Short identifiers consist of ASCII letters (A-Za-z), digits (0-9), full stops (.) and hyphen or minus signs (-) <br/>'
                                        '\u2022 Short identifiers consist of an abbreviation based on a common short name or acronym for the license or exception. <br/>'
                                        '\u2022 Where applicable, the abbreviation will be followed by a dash and then the version number, in X.Y format. <br/>'
                                        '\u2022 Where applicable, and if possible, the short identifier should be harmonized with other well-known open source naming sources (i.e., OSI, Fedora, etc.) <br/>'
                                        '\u2022 Short identifiers should be as short in length as possible while staying consistent with all other naming criteria.')

SOURCE_URL_HELP_TEXT = mark_safe('\u2022 Include URL for the official text of the license or exception.<br />'
                                '\u2022 If the license is OSI approved, also include URL for OSI license page.<br />'
                                '\u2022 Include another URL that has text version of license, if neither of the first two options are available.<br />'
                                '\u2022 Note that the source URL may refer to an original URL for the license which is no longer active. We don\'t remove inactive URLs. New or best available URLs may be added.<br />'
                                '\u2022 Link to the license or exception in its native language is used where specified (e.g. French for CeCILL). Link to English version where multiple, equivalent official translations (e.g. EUPL)')

LICENSE_HEADER_INFO_HELP_TEXT = mark_safe('\u2022 Should only include text intended to be put in the header of source files or other files as specified in the license or license appendix when specifically delineated.<br />'
                                            '\u2022 Indicate if there is any variation in the header (i.e. for files developed by a contributor versus when applying license to original work) <br />'
                                            '\u2022 Do not include NOTICE info intended for a separate notice file.<br />'
                                            '\u2022 Leave this field blank if there is no standard header as specifically defined in the license.')

COMMENTS_INFO_HELP_TEXT = mark_safe('\u2022 Provide a short explanation regarding the need for this license or exception to be included on the SPDX License List. <br />'
                                    '\u2022 Identify at least one program that uses it or any other related information.')

LICENSE_TEXT_HELP_TEXT = mark_safe('Full license of the license text.')


# License namespace submission form help text

LIC_NS_SUB_FULLNAME_HELP_TEXT = mark_safe('\u2022 The full name of the license namespace submitter.')

LIC_NS_NSINFO_HELP_TEXT = mark_safe('\u2022 License namespace in dns-style request or a free-format.')

LIC_NS_NSID_HELP_TEXT = mark_safe('\u2022 License namespace short identifier.')

LIC_NS_URL_INFO_HELP_TEXT = mark_safe('\u2022 Include URL for the official text of the license namespace.')

LIC_NS_LIC_LIST_URL_HELP_TEXT = mark_safe('\u2022 Include URL for the official text of the license list namespace.')

LIC_NS_GH_REPO_URL_HELP_TEXT = mark_safe('\u2022 Include URL for the official github page of the license namespace.')

LIC_NS_ORG_HELP_TEXT = mark_safe('\u2022 Select organisation of the license namespace.')

LIC_NS_DESC_HELP_TEXT = mark_safe('Description of the license namespace')
