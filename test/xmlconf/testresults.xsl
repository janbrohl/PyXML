<?xml version="1.0" encoding="ISO-8859-1"?>
<!--
    Format a test result report to HTML.

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>

    The output format is based on the test reports at
    http://xmlconf.sourceforge.net/xml/?selected=java

    $Id: testresults.xsl,v 1.2 2001/09/06 22:23:38 jhermann Exp $
-->

<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0"
>

  <xsl:output method="html" encoding="ISO-8859-1" indent="no"/>

  <!--====================================================================-->
  <!--= MAIN REPORT PAGE =================================================-->
  <!--====================================================================-->

  <xsl:template match="REPORT">
    <html>
      <head>
        <title><xsl:value-of select="PARSER"/> Conformance Report</title>
        <style type="text/css"><xsl:comment>
h1, h2, h3, h4, h5, h6 {
  color: maroon;
  text-align: center;
}
dl,ul,ol {
    margin-top: 1pt;
}
//</xsl:comment>
        </style>
      </head>

      <body bgcolor="#eeeeff">

        <h1>XML Processor Conformance Report:<br clear="none" />
            <em><xsl:value-of select="PARSER"/></em></h1>

        <xsl:call-template name="testinfo"/>
        <xsl:call-template name="summary"/>

        <p> Sections of this report are:
        <a href="#explanation" shape="rect">Explanation of Tables</a>;
        <a href="#positive" shape="rect">Positive Tests</a>, cases where this processor should
        report no errors;
        <a href="#negative" shape="rect">Negative Tests</a>, documents for which this processor
        must report the known errors; and
        <a href="#optional" shape="rect">Informative Tests</a>, documents with errors which
        processors are not required to report. </p>

        <xsl:if test="count(MEMO) != 0">
          Test harness messages:
            <ul>
              <xsl:apply-templates select="MEMO"/>
            </ul>
        </xsl:if>

        <h2><a name="explanation" shape="rect">Explanation of Tables</a></h2>

        <p>Sections presenting test results are composed largely of tables, with
        explanations focussing on exactly what those tables indicate. "Section",
        "Test ID" and "Description" are the related fields from the test definition.
        "Mode" indicates the parsing mode ""NV" for non-validating, and "V" for validating.
        </p>

        <p>
        "Diagnostic" consists of the output of the test harness, indicating the type of error.
        The following list shows the usual keywords that allow you to categorize the
        message, the exact output depends on the test harness.
        </p>

        <dl>
            <dt><b>FATAL</b></dt>
            <dd>The diagnostic was reported as a fatal error.  Such errors are
            primarily well-formedness errors, such as the violation of XML 1.0
            syntax rules or of well formedness constraints.
            <em>In some underfeatured parser APIs, this may be the
            only kind of error that gets reported.</em>
            </dd>
            <dt><b>ERROR</b></dt>
            <dd>The diagnostic was reported as a recoverable error.  Such
            errors primarily used to report validation errors, which are all
            violations of validity constraints, but some other errors are also
            classed as nonfatal.</dd>
            <dt><b>WARNING</b></dt>
            <dd>The diagnostic was reported as a warning; warnings are purely
            informative and may be emitted in a number of cases identified by
            the XML 1.0 specification (as well as in other cases).</dd>
        </dl>

        <p> Other comments may indicate other categories of conformance issue.
        For example, some errors relate to problematic implementation of SAX;
        and in exceptional cases, the harness can be forced to report a failure
        on some test. </p>

        <dl>
            <dt><b>EXCEPTION</b></dt>
            <dd>This indicates an exception outside of the above three classes
            of errors; such messages are outside the SAX specification and most
            often indicate either a problem within the parser (it should map
            the exception to a call of the error handler) or a problem with the
            test itself (like a missing file).</dd>
        </dl>

        <p> In all cases, negative tests that appear to pass must be individually
        examined in the report below.
        The diagnostic provided by the processor must correspond to the description
        of the test provided; if the processor does not report the matching error,
        the seeming "pass" is in fact an error of a type the test harness could
        not detect or report.  That error is either a conformance bug, or an error
        in the diagnostic being produced; or, rarely, both.</p>

        <!--==============================================================-->
        <h2><a name="positive" shape="rect">Positive Tests</a></h2>
        <p>All conformant XML 1.0 processors must accept "valid" input documents
        without reporting any errors, and moreover must report the correct output
        data to the application when processing those documents.  Nonvalidating
        processors must also accept "invalid" input documents without reporting any errors.
        These are called "Positive Tests" because they ensure that the processor
        just "does the right thing" without reporting any problems.</p>

        <p>In the interest of brevity, the only tests listed here are those which
        produce diagnostics of some kind, such as test failures.  In some cases,
        warnings may be reported when processing these documents, but these do not
        indicate failures.</p>

        <p>No interpretation of these results is necessary; every "error" or
        "fatal" message presented here is an XML conformance failure.  Maintainers
        of an XML processor will generally want to fix their software so that it
        conforms fully to the XML specification.</p>
    
        <h3>Valid Documents</h3>
        <p>All XML processors must accept all valid documents.  This group
        of tests must accordingly produce no test failures.</p>

        <xsl:call-template name="results">
          <xsl:with-param name="testruns" select="TESTRESULT[TEST/@TYPE = 'valid']/TESTRUN[@SEVERITY != 'success']"/>
        </xsl:call-template>

        <!--==============================================================-->
        <h2><a name="negative" shape="rect">Negative Tests</a></h2>
        <p> All conformant XML 1.0 processors must reject documents which are not
        well-formed.  In addition, validating processors
        must report the validity errors for invalid documents.
        These are called <em>Negative Tests</em> because the test is intended
        to establish that errors are reported when they should be.
        </p>

        <p> Moreover, the processor must both fail for the appropriate reason (given
        by the parser diagnostic) and must report an error at the right level ("error"
        or "fatal").  If both criteria were not considered, a processor which failed
        frequently (such as by failing to parse any document at all) would appear to
        pass a large number of conformance tests   Unfortunately, the test driver can
        only tell whether the error was reported at the right level.  It can't
        determine whether the processor failed for the right reason. </p>

        <p> That's where a person to interpret these test results is critical.  Such
        a person analyses the diagnostics, reported here, for negative tests not
        already known to be failures (for not reporting an error, or reporting one
        at the wrong level).  If the diagnostic reported for such tests doesn't match
        the failure from the test description, there is an error in the diagnostic or
        in the processor's XML conformance (or sometimes in both).</p>

        <h3>Invalid Documents</h3>

        <p> Validating processors must correctly report "error" diagnostics
        for all documents which are well formed but invalid.  Such errors must
        also be, "at user option", recoverable so that the validating parser
        may be used in a nonvalidating mode by ignoring all validity errors.
        <em>Some parser APIs do not support recoverability.</em>
        Such issues should be noted in the documentation for the API, and
        for its test harness.
        </p>

        <xsl:call-template name="results">
          <xsl:with-param name="testruns" select="TESTRESULT[TEST/@TYPE = 'invalid']/TESTRUN[@SEVERITY != 'success']"/>
        </xsl:call-template>

        <!--==============================================================-->
        <h3>Documents which are not Well-Formed</h3>

        <p>All XML processors must correctly reject (with a "fatal"
        error) all XML documents which are not well-formed.</p>

        <xsl:call-template name="results">
          <xsl:with-param name="testruns" select="TESTRESULT[TEST/@TYPE = 'not-wf']/TESTRUN[@SEVERITY != 'success']"/>
        </xsl:call-template>

        <!--==============================================================-->
        <h2><a name="optional" shape="rect">Informative Tests</a></h2>

        <p> Certain XML documents are specified to be errors, but the handling
        of those documents is not fully determined by the XML 1.0 specification.
        As a rule, these errors may be reported in any manner whatsoever, or
        completely ignored, without consequence in terms of conformance to the
        XML 1.0 specification.  And some of these documents don't have errors;
        documents in encodings other than UTF-8 and UTF-16 are legal, but not
        all processors are required to parse them.  </p>

        <p>Such "optional" errors are listed here for informational purposes, since
        processors which ignore such errors may cause document creators to create
        documents which are not accepted by all conformant XML 1.0 processors.
        (And of course, processors which produce incorrect diagnostics for such
        cases should be avoided.) </p>

        <xsl:call-template name="results">
          <xsl:with-param name="testruns" select="TESTRESULT[TEST/@TYPE = 'error']/TESTRUN[@SEVERITY != 'success']"/>
        </xsl:call-template>

      </body>
    </html>
  </xsl:template>

  <xsl:template match="MEMO">
    <li><xsl:apply-templates/></li>
  </xsl:template>


  <!--====================================================================-->
  <!--= GENERAL TEST INFORMATION =========================================-->
  <!--====================================================================-->

  <xsl:template name="testinfo">
    <p>This document is the output of an
    <a href="http://xmlconf.sourceforge.net/" shape="rect">XML test harness</a>.
    It reports on the conformance of the following configuration: </p>

    <center><table bgcolor="#ffffff" cellpadding="4" border="1">
      <xsl:call-template name="testinfo-row">
        <xsl:with-param name="label" select="'XML Parser'"/>
        <xsl:with-param name="value" select="PARSER"/>
      </xsl:call-template>
      <xsl:call-template name="testinfo-row">
        <xsl:with-param name="label" select="'Test Harness'"/>
        <xsl:with-param name="value" select="HARNESS"/>
      </xsl:call-template>
      <xsl:call-template name="testinfo-row">
        <xsl:with-param name="label" select="'Runtime Environment'"/>
        <xsl:with-param name="value" select="RUNTIME"/>
      </xsl:call-template>
      <xsl:call-template name="testinfo-row">
        <xsl:with-param name="label" select="'Host OS Info'"/>
        <xsl:with-param name="value" select="PLATFORM"/>
      </xsl:call-template>
      <xsl:call-template name="testinfo-row">
        <xsl:with-param name="label" select="'Suite of Testcases'"/>
        <xsl:with-param name="value" select="@PROFILE"/>
      </xsl:call-template>
      <xsl:call-template name="testinfo-row">
        <xsl:with-param name="label" select="'Test Run Date'"/>
        <xsl:with-param name="value" select="@DATE"/>
      </xsl:call-template>
    </table></center>
  </xsl:template>

  <xsl:template name="testinfo-row">
    <xsl:param name="label"/>
    <xsl:param name="value"/>
    <tr>
      <td bgcolor="#ffffcc" colspan="1" rowspan="1"><xsl:value-of select="$label"/></td>
      <td colspan="1" rowspan="1"><xsl:value-of select="$value"/></td>
    </tr>
  </xsl:template>


  <!--====================================================================-->
  <!--= SUMMARY INFORMATION ==============================================-->
  <!--====================================================================-->

  <xsl:template name="summary">
    <p> A summary of test results follows.  To know the actual test status,
    <b>someone must examine the result of each passed negative test</b>
    (and informative test) to make sure it failed for the right reason.
    That examination may cause the counts of failed tests to increase
    (and passed tests to decrease), changing a provisional "conforms" status
    to a "does not conform".  </p>

    <center><table bgcolor="#ffffff" cellpadding="4" border="1">
      <tr>
        <td bgcolor="#ffffcc" colspan="1" rowspan="1"><b>Summary</b></td>
        <td bgcolor="#ffffcc" colspan="1" rowspan="1">Validating</td>
        <td bgcolor="#ffffcc" colspan="1" rowspan="1">Non-Validating</td>
      </tr>
      <xsl:call-template name="summary-row">
        <xsl:with-param name="label" select="'Total Tests'"/>
        <xsl:with-param name="val" select="count(TESTRESULT/TESTRUN[@PARSER-TYPE='validating'])"/>
        <xsl:with-param name="nval" select="count(TESTRESULT/TESTRUN[@PARSER-TYPE='non-validating'])"/>
      </xsl:call-template>
      <xsl:call-template name="summary-row">
        <xsl:with-param name="label" select="'Sucessful Tests'"/>
        <xsl:with-param name="val" select="count(TESTRESULT/TESTRUN[@PARSER-TYPE='validating' and @SEVERITY='success'])"/>
        <xsl:with-param name="nval" select="count(TESTRESULT/TESTRUN[@PARSER-TYPE='non-validating' and @SEVERITY='success'])"/>
      </xsl:call-template>
      <xsl:call-template name="summary-row">
        <xsl:with-param name="label" select="'Important Failures'"/>
        <xsl:with-param name="val" select="count(TESTRESULT/TESTRUN[@PARSER-TYPE='validating' and (@SEVERITY='high' or @SEVERITY='medium')])"/>
        <xsl:with-param name="nval" select="count(TESTRESULT/TESTRUN[@PARSER-TYPE='non-validating' and (@SEVERITY='high' or @SEVERITY='medium')])"/>
      </xsl:call-template>
      <xsl:call-template name="summary-row">
        <xsl:with-param name="label" select="'Ignorable Failures'"/>
        <xsl:with-param name="val" select="count(TESTRESULT/TESTRUN[@PARSER-TYPE='validating' and @SEVERITY='low'])"/>
        <xsl:with-param name="nval" select="count(TESTRESULT/TESTRUN[@PARSER-TYPE='non-validating' and @SEVERITY='low'])"/>
      </xsl:call-template>
    </table></center>

  </xsl:template>

  <xsl:template name="summary-row">
    <xsl:param name="label"/>
    <xsl:param name="val"/>
    <xsl:param name="nval"/>
    <tr>
      <td bgcolor="#ffffcc" colspan="1" rowspan="1"><xsl:value-of select="$label"/></td>
      <td align="right" colspan="1" rowspan="1"><xsl:value-of select="$val"/></td>
      <td align="right" colspan="1" rowspan="1"><xsl:value-of select="$nval"/></td>
    </tr>
  </xsl:template>


  <!--====================================================================-->
  <!--= INDIVIDUAL TEST RESULTS ==========================================-->
  <!--====================================================================-->

  <xsl:template name="results">
    <xsl:param name="testruns"/>
    <p>There are <b><xsl:value-of select="count($testruns)"/></b> failures of this type.</p>
    <xsl:if test="count($testruns) != 0">
      <table width="100%" bgcolor="#ffffff" cellpadding="4" border="1">
        <tr>
          <td bgcolor="#ffffcc" colspan="1" rowspan="1">Section and [Rules]</td>
          <td bgcolor="#ffffcc" colspan="1" rowspan="1">Test ID</td>
          <td bgcolor="#ffffcc" colspan="1" rowspan="1">Mode</td>
          <td bgcolor="#ffffcc" colspan="1" rowspan="1">Description</td>
          <td bgcolor="#ffffcc" colspan="1" rowspan="1">Diagnostic</td>
        </tr>
        <xsl:apply-templates select="$testruns"/>
      </table>
    </xsl:if> 
  </xsl:template>

  <xsl:template match="TESTRUN">
    <tr valign="top">
      <td><xsl:value-of select="../TEST/@SECTIONS"/></td>
      <td><xsl:value-of select="../TEST/@ID"/></td>
      <td><xsl:if test="starts-with(@PARSER-TYPE,'non-')">N</xsl:if>V</td>
      <td><xsl:apply-templates select="../TEST"/></td>
      <td><xsl:apply-templates mode="break"/></td>
    </tr>
  </xsl:template>


  <!--====================================================================-->
  <!--= TEXT LAYOUT ======================================================-->
  <!--====================================================================-->

  <xsl:template match="text()" mode="break">
    <xsl:call-template name="break-text">
      <xsl:with-param name="text" select="."/>
    </xsl:call-template>
  </xsl:template>

  <!-- Remove "break" mode for element nodes -->
  <xsl:template match="*" mode="break">
    <xsl:apply-templates select="."/>
  </xsl:template>

  <xsl:template name="break-text">
    <xsl:param name="text"/>
    <xsl:choose>
      <xsl:when test="contains($text,'&#10;')">
        <xsl:if test="normalize-space(substring-before($text,'&#10;'))">
          <xsl:value-of select="substring-before($text,'&#10;')"/><br/>
        </xsl:if>
        <xsl:call-template name="break-text">
          <xsl:with-param name="text" select="substring-after($text,'&#10;')"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text"/>
      </xsl:otherwise> 
    </xsl:choose> 
  </xsl:template>

  <xsl:template match="B">
    <strong><xsl:apply-templates/></strong>
  </xsl:template>

  <xsl:template match="EM">
    <em><xsl:apply-templates/></em>
  </xsl:template>


</xsl:stylesheet>

