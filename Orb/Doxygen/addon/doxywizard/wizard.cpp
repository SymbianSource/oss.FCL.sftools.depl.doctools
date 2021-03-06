#include "wizard.h"
#include "input.h"
#include "doxywizard.h"

#include <QtGui>

// step1 options
#define STR_PROJECT_NAME          QString::fromAscii("PROJECT_NAME")
#define STR_INPUT                 QString::fromAscii("INPUT")
#define STR_OUTPUT_DIRECTORY      QString::fromAscii("OUTPUT_DIRECTORY")
#define STR_PROJECT_NUMBER        QString::fromAscii("PROJECT_NUMBER")
#define STR_RECURSIVE             QString::fromAscii("RECURSIVE")
#define STR_OPTIMIZE_OUTPUT_FOR_C QString::fromAscii("OPTIMIZE_OUTPUT_FOR_C")
#define STR_OPTIMIZE_OUTPUT_JAVA  QString::fromAscii("OPTIMIZE_OUTPUT_JAVA")
#define STR_OPTIMIZE_FOR_FORTRAN  QString::fromAscii("OPTIMIZE_FOR_FORTRAN")
#define STR_OPTIMIZE_OUTPUT_VHDL  QString::fromAscii("OPTIMIZE_OUTPUT_VHDL")
#define STR_CPP_CLI_SUPPORT       QString::fromAscii("CPP_CLI_SUPPORT")
#define STR_HIDE_SCOPE_NAMES      QString::fromAscii("HIDE_SCOPE_NAMES")
#define STR_EXTRACT_ALL           QString::fromAscii("EXTRACT_ALL")
#define STR_SOURCE_BROWSER        QString::fromAscii("SOURCE_BROWSER")
#define STR_GENERATE_HTML         QString::fromAscii("GENERATE_HTML")
#define STR_GENERATE_LATEX        QString::fromAscii("GENERATE_LATEX")
#define STR_GENERATE_MAN          QString::fromAscii("GENERATE_MAN")
#define STR_GENERATE_RTF          QString::fromAscii("GENERATE_RTF")
#define STR_GENERATE_XML          QString::fromAscii("GENERATE_XML")
#define STR_GENERATE_HTMLHELP     QString::fromAscii("GENERATE_HTMLHELP")
#define STR_GENERATE_TREEVIEW     QString::fromAscii("GENERATE_TREEVIEW")
#define STR_USE_PDFLATEX          QString::fromAscii("USE_PDFLATEX")
#define STR_PDF_HYPERLINKS        QString::fromAscii("PDF_HYPERLINKS")
#define STR_SEARCHENGINE          QString::fromAscii("SEARCHENGINE")
#define STR_HAVE_DOT              QString::fromAscii("HAVE_DOT")
#define STR_CLASS_DIAGRAMS        QString::fromAscii("CLASS_DIAGRAMS")
#define STR_CLASS_GRAPH           QString::fromAscii("CLASS_GRAPH")
#define STR_COLLABORATION_GRAPH   QString::fromAscii("COLLABORATION_GRAPH")
#define STR_GRAPHICAL_HIERARCHY   QString::fromAscii("GRAPHICAL_HIERARCHY")
#define STR_INCLUDE_GRAPH         QString::fromAscii("INCLUDE_GRAPH")
#define STR_INCLUDED_BY_GRAPH     QString::fromAscii("INCLUDED_BY_GRAPH")
#define STR_CALL_GRAPH            QString::fromAscii("CALL_GRAPH")
#define STR_CALLER_GRAPH          QString::fromAscii("CALLER_GRAPH")


static bool g_optimizeMapping[6][6] = 
{
  // A: OPTIMIZE_OUTPUT_FOR_C
  // B: OPTIMIZE_OUTPUT_JAVA
  // C: OPTIMIZE_FOR_FORTRAN
  // D: OPTIMIZE_OUTPUT_VHDL
  // E: CPP_CLI_SUPPORT
  // F: HIDE_SCOPE_NAMES
  // A     B     C     D     E      F
  { false,false,false,false,false,false }, // 0: C++
  { false,false,false,false,true, false }, // 1: C++/CLI
  { false,true, false,false,false,false }, // 2: C#/Java
  { true, false,false,false,false,true  }, // 3: C/PHP 
  { false,false,true, false,false,false }, // 4: Fortran
  { false,false,false,true, false,false }, // 5: VHDL
};

static QString g_optimizeOptionNames[6] =
{
  STR_OPTIMIZE_OUTPUT_FOR_C,
  STR_OPTIMIZE_OUTPUT_JAVA,
  STR_OPTIMIZE_FOR_FORTRAN,
  STR_OPTIMIZE_OUTPUT_VHDL,
  STR_CPP_CLI_SUPPORT,
  STR_HIDE_SCOPE_NAMES
};

//==========================================================================

static bool stringVariantToBool(const QVariant &v)
{
  QString s = v.toString().toLower();
  return s==QString::fromAscii("yes") || s==QString::fromAscii("true") || s==QString::fromAscii("1");
} 

static bool getBoolOption(
    const QHash<QString,Input*>&model,const QString &name)
{
  Input *option = model[name];
  Q_ASSERT(option!=0);
  return stringVariantToBool(option->value());
} 

static QString getStringOption(
    const QHash<QString,Input*>&model,const QString &name)
{
  Input *option = model[name];
  Q_ASSERT(option!=0);
  return option->value().toString();
}

static void updateBoolOption(
    const QHash<QString,Input*>&model,const QString &name,bool bNew)
{
  Input *option = model[name];
  Q_ASSERT(option!=0);
  bool bOld = stringVariantToBool(option->value());
  if (bOld!=bNew)
  {
    option->value()=QString::fromAscii(bNew ? "true" : "false");
    option->update();
  }
}

static void updateStringOption(
    const QHash<QString,Input*>&model,const QString &name,const QString &s)
{
  Input *option = model[name];
  Q_ASSERT(option!=0);
  if (option->value().toString()!=s)
  {
    option->value() = s;
    option->update();
  }
}

//==========================================================================

Step1::Step1(Wizard *wizard,const QHash<QString,Input*> &modelData) : m_wizard(wizard), m_modelData(modelData)
{
  QVBoxLayout *layout = new QVBoxLayout(this);
  layout->setMargin(4);
  layout->setSpacing(8);
  QLabel *l = new QLabel(this);
  l->setText(tr("Provide some information "
              "about the project you are documenting"));
  layout->addWidget(l);
  QWidget *w      = new QWidget( this );
  QHBoxLayout *bl = new QHBoxLayout(w);
  bl->setSpacing(10);

  QWidget *col1 = new QWidget;
  QVBoxLayout *col1Layout = new QVBoxLayout(col1);
  col1Layout->setSpacing(8);
  QLabel *projName = new QLabel(this);
  projName->setText(tr("Project name:"));
  projName->setAlignment(Qt::AlignRight|Qt::AlignVCenter);
  QLabel *projVersion = new QLabel(this);
  projVersion->setText(tr("Project version or id:"));
  projVersion->setAlignment(Qt::AlignRight|Qt::AlignVCenter);
  col1Layout->addWidget(projName);
  col1Layout->addWidget(projVersion);

  QWidget *col2 = new QWidget;
  QVBoxLayout *col2Layout = new QVBoxLayout(col2);
  col2Layout->setSpacing(8);
  m_projName = new QLineEdit;
  m_projNumber = new QLineEdit;
  col2Layout->addWidget(m_projName);
  col2Layout->addWidget(m_projNumber);

  bl->addWidget(col1);
  bl->addWidget(col2);
  w->setLayout(bl);

  layout->addWidget(w);

  //---------------------------------------------------
  QFrame *f = new QFrame( this );
  f->setFrameStyle( QFrame::HLine | QFrame::Sunken );
  layout->addWidget(f);
  
  l = new QLabel(this);
  l->setText(tr("Specify the directory to scan for source code"));
  layout->addWidget(l);
  QWidget *row = new QWidget;
  QHBoxLayout *rowLayout = new QHBoxLayout(row);
  rowLayout->setSpacing(10);
  l = new QLabel(this);
  l->setText(tr("Source code directory:"));
  rowLayout->addWidget(l);
  m_sourceDir = new QLineEdit;
  m_srcSelectDir = new QPushButton(this);
  m_srcSelectDir->setText(tr("Select..."));
  rowLayout->addWidget(m_sourceDir);
  rowLayout->addWidget(m_srcSelectDir);
  layout->addWidget(row);

  m_recursive = new QCheckBox(this);
  m_recursive->setText(tr("Scan recursively"));
  m_recursive->setChecked(TRUE);
  layout->addWidget(m_recursive);

  //---------------------------------------------------
  f = new QFrame( this );
  f->setFrameStyle( QFrame::HLine | QFrame::Sunken );
  layout->addWidget(f);

  l = new QLabel(this);
  l->setText(tr("Specify the directory where doxygen should "
              "put the generated documentation"));
  layout->addWidget(l);
  row = new QWidget;
  rowLayout = new QHBoxLayout(row);
  rowLayout->setSpacing(10);
  l = new QLabel(this);
  l->setText(tr("Destination directory:"));
  rowLayout->addWidget(l);
  m_destDir = new QLineEdit;
  m_dstSelectDir = new QPushButton(this);
  m_dstSelectDir->setText(tr("Select..."));
  rowLayout->addWidget(m_destDir);
  rowLayout->addWidget(m_dstSelectDir);
  layout->addWidget(row);
  layout->addStretch(1);
  setLayout(layout);

  connect(m_srcSelectDir,SIGNAL(clicked()),
          this,SLOT(selectSourceDir()));
  connect(m_dstSelectDir,SIGNAL(clicked()),
          this,SLOT(selectDestinationDir()));
  connect(m_projName,SIGNAL(textChanged(const QString &)),SLOT(setProjectName(const QString &)));
  connect(m_projNumber,SIGNAL(textChanged(const QString &)),SLOT(setProjectNumber(const QString &)));
  connect(m_sourceDir,SIGNAL(textChanged(const QString &)),SLOT(setSourceDir(const QString &)));
  connect(m_recursive,SIGNAL(stateChanged(int)),SLOT(setRecursiveScan(int)));
  connect(m_destDir,SIGNAL(textChanged(const QString &)),SLOT(setDestinationDir(const QString &)));
}

void Step1::selectSourceDir()
{
  QString path = QFileInfo(MainWindow::instance().configFileName()).path();
  QString dirName = QFileDialog::getExistingDirectory(this,
        tr("Select source directory"),path);
  QDir dir(path);
  if (!MainWindow::instance().configFileName().isEmpty() && dir.exists())
  {
    dirName = dir.relativeFilePath(dirName);
  }
  if (dirName.isEmpty())
  {
    dirName=QString::fromAscii(".");
  }
  m_sourceDir->setText(dirName);
}

void Step1::selectDestinationDir()
{
  QString path = QFileInfo(MainWindow::instance().configFileName()).path();
  QString dirName = QFileDialog::getExistingDirectory(this,
        tr("Select destination directory"),path);
  QDir dir(path);
  if (!MainWindow::instance().configFileName().isEmpty() && dir.exists())
  {
    dirName = dir.relativeFilePath(dirName);
  }
  if (dirName.isEmpty())
  {
    dirName=QString::fromAscii(".");
  }
  m_destDir->setText(dirName);
}

void Step1::setProjectName(const QString &name)
{
  updateStringOption(m_modelData,STR_PROJECT_NAME,name);
}

void Step1::setProjectNumber(const QString &num)
{
  updateStringOption(m_modelData,STR_PROJECT_NUMBER,num);
}

void Step1::setSourceDir(const QString &dir)
{
  Input *option = m_modelData[STR_INPUT];
  if (option->value().toStringList().count()>0)
  {
    QStringList sl = option->value().toStringList();
    if (sl[0]!=dir)
    {
      sl[0] = dir;
      option->value() = sl;
      option->update();
    }
  }
  else
  {
    option->value() = QStringList() << dir;
    option->update();
  }
}

void Step1::setDestinationDir(const QString &dir)
{
  updateStringOption(m_modelData,STR_OUTPUT_DIRECTORY,dir);
}

void Step1::setRecursiveScan(int s)
{
  updateBoolOption(m_modelData,STR_RECURSIVE,s==Qt::Checked);
}

void Step1::init()
{
  Input *option;
  m_projName->setText(getStringOption(m_modelData,STR_PROJECT_NAME));
  m_projNumber->setText(getStringOption(m_modelData,STR_PROJECT_NUMBER));
  option = m_modelData[STR_INPUT];
  if (option->value().toStringList().count()>0)
  {
    m_sourceDir->setText(option->value().toStringList().first());
  }
  m_recursive->setChecked(
      getBoolOption(m_modelData,STR_RECURSIVE) ? Qt::Checked : Qt::Unchecked);
  m_destDir->setText(getStringOption(m_modelData,STR_OUTPUT_DIRECTORY));
}


//==========================================================================

Step2::Step2(Wizard *wizard,const QHash<QString,Input*> &modelData) 
  : m_wizard(wizard), m_modelData(modelData)
{
  QRadioButton *r;
  QVBoxLayout *layout = new QVBoxLayout(this);

  //---------------------------------------------------
  m_extractModeGroup = new QButtonGroup(this);
  m_extractMode = new QGroupBox(this);
  m_extractMode->setTitle(tr("Select the desired extraction mode:"));
  QGridLayout *gbox = new QGridLayout( m_extractMode );
  r = new QRadioButton(tr("Documented entities only"));
  r->setChecked(true);
  m_extractModeGroup->addButton(r, 0);
  gbox->addWidget(r,1,0);
  // 1 -> EXTRACT_ALL = NO
  r = new QRadioButton(tr("All Entities"));
  m_extractModeGroup->addButton(r, 1);
  gbox->addWidget(r,2,0);
  // 2 -> EXTRACT_ALL = YES
  m_crossRef = new QCheckBox(m_extractMode);
  m_crossRef->setText(tr("Include cross-referenced source code in the output"));
  // m_crossRef -> SOURCE_BROWSER = YES/NO
  gbox->addWidget(m_crossRef,3,0);
  layout->addWidget(m_extractMode);
  
  //---------------------------------------------------
  QFrame *f = new QFrame( this );
  f->setFrameStyle( QFrame::HLine | QFrame::Sunken );
  layout->addWidget(f);

  m_optimizeLangGroup = new QButtonGroup(this);
  m_optimizeLang = new QGroupBox(this);
  m_optimizeLang->setTitle(tr("Select programming language to optimize the results for"));
  gbox = new QGridLayout( m_optimizeLang ); 
  
  r = new QRadioButton(m_optimizeLang);
  r->setText(tr("Optimize for C++ output"));
  r->setChecked(true);
  m_optimizeLangGroup->addButton(r, 0);
  // 0 -> OPTIMIZE_OUTPUT_FOR_C = NO
  //      OPTIMIZE_OUTPUT_JAVA  = NO
  //      OPTIMIZE_FOR_FORTRAN  = NO
  //      OPTIMIZE_OUTPUT_VHDL  = NO
  //      CPP_CLI_SUPPORT       = NO
  //      HIDE_SCOPE_NAMES      = NO
  gbox->addWidget(r,0,0);
  r = new QRadioButton(tr("Optimize for C++/CLI output"));
  gbox->addWidget(r,1,0);
  m_optimizeLangGroup->addButton(r, 1);
  // 1 -> OPTIMIZE_OUTPUT_FOR_C = NO
  //      OPTIMIZE_OUTPUT_JAVA  = NO
  //      OPTIMIZE_FOR_FORTRAN  = NO
  //      OPTIMIZE_OUTPUT_VHDL  = NO
  //      CPP_CLI_SUPPORT       = YES
  //      HIDE_SCOPE_NAMES      = NO
  r = new QRadioButton(tr("Optimize for Java or C# output"));
  m_optimizeLangGroup->addButton(r, 2);
  // 2 -> OPTIMIZE_OUTPUT_FOR_C = NO
  //      OPTIMIZE_OUTPUT_JAVA  = YES
  //      OPTIMIZE_FOR_FORTRAN  = NO
  //      OPTIMIZE_OUTPUT_VHDL  = NO
  //      CPP_CLI_SUPPORT       = NO
  //      HIDE_SCOPE_NAMES      = NO
  gbox->addWidget(r,2,0);
  r = new QRadioButton(tr("Optimize for C or PHP output"));
  m_optimizeLangGroup->addButton(r, 3);
  // 3 -> OPTIMIZE_OUTPUT_FOR_C = YES
  //      OPTIMIZE_OUTPUT_JAVA  = NO
  //      OPTIMIZE_FOR_FORTRAN  = NO
  //      OPTIMIZE_OUTPUT_VHDL  = NO
  //      CPP_CLI_SUPPORT       = NO
  //      HIDE_SCOPE_NAMES      = YES
  gbox->addWidget(r,3,0);
  r = new QRadioButton(tr("Optimize for Fortran output"));
  m_optimizeLangGroup->addButton(r, 4);
  // 4 -> OPTIMIZE_OUTPUT_FOR_C = NO
  //      OPTIMIZE_OUTPUT_JAVA  = NO
  //      OPTIMIZE_FOR_FORTRAN  = YES
  //      OPTIMIZE_OUTPUT_VHDL  = NO
  //      CPP_CLI_SUPPORT       = NO
  //      HIDE_SCOPE_NAMES      = NO
  gbox->addWidget(r,4,0);
  r = new QRadioButton(tr("Optimize for VHDL output"));
  m_optimizeLangGroup->addButton(r, 5);
  // 5 -> OPTIMIZE_OUTPUT_FOR_C = NO
  //      OPTIMIZE_OUTPUT_JAVA  = NO
  //      OPTIMIZE_FOR_FORTRAN  = NO
  //      OPTIMIZE_OUTPUT_VHDL  = YES
  //      CPP_CLI_SUPPORT       = NO
  //      HIDE_SCOPE_NAMES      = NO
  gbox->addWidget(r,5,0);

  layout->addWidget(m_optimizeLang);
  layout->addStretch(1);

  connect(m_crossRef,SIGNAL(stateChanged(int)),
          SLOT(changeCrossRefState(int)));
  connect(m_optimizeLangGroup,SIGNAL(buttonClicked(int)),
          SLOT(optimizeFor(int)));
  connect(m_extractModeGroup,SIGNAL(buttonClicked(int)),
          SLOT(extractMode(int)));
}


void Step2::optimizeFor(int choice)
{
  for (int i=0;i<6;i++)
  {
    updateBoolOption(m_modelData,
                     g_optimizeOptionNames[i],
                     g_optimizeMapping[choice][i]);
  }
}

void Step2::extractMode(int choice)
{
  updateBoolOption(m_modelData,STR_EXTRACT_ALL,choice==1);
}

void Step2::changeCrossRefState(int choice)
{
  updateBoolOption(m_modelData,STR_SOURCE_BROWSER,choice==Qt::Checked);
}

void Step2::init()
{
  m_extractModeGroup->button(
      getBoolOption(m_modelData,STR_EXTRACT_ALL) ? 1 : 0)->setChecked(true);
  m_crossRef->setChecked(getBoolOption(m_modelData,STR_SOURCE_BROWSER));

  int x=0;
  if (getBoolOption(m_modelData,STR_CPP_CLI_SUPPORT))            x=1;
  else if (getBoolOption(m_modelData,STR_OPTIMIZE_OUTPUT_JAVA))  x=2;
  else if (getBoolOption(m_modelData,STR_OPTIMIZE_OUTPUT_FOR_C)) x=3;
  else if (getBoolOption(m_modelData,STR_OPTIMIZE_FOR_FORTRAN))  x=4;
  else if (getBoolOption(m_modelData,STR_OPTIMIZE_OUTPUT_VHDL))  x=5;
  m_optimizeLangGroup->button(x)->setChecked(true);
}

//==========================================================================

Step3::Step3(Wizard *wizard,const QHash<QString,Input*> &modelData) 
  : m_wizard(wizard), m_modelData(modelData)
{
  QVBoxLayout *vbox = 0;
  QRadioButton *r   = 0;

  QGridLayout *gbox = new QGridLayout( this );
  gbox->addWidget(new QLabel(tr("Select the output format(s) to generate")),0,0);
  {
    m_htmlOptions = new QGroupBox(tr("HTML"));
    m_htmlOptions->setCheckable(true);
    // GENERATE_HTML
    m_htmlOptionsGroup = new QButtonGroup(m_htmlOptions);
    QRadioButton *r = new QRadioButton(tr("plain HTML"));
    r->setChecked(true);
    m_htmlOptionsGroup->addButton(r, 0);
    vbox = new QVBoxLayout;
    vbox->addWidget(r);
    r = new QRadioButton(tr("with frames and a navigation tree"));
    m_htmlOptionsGroup->addButton(r, 1);
    // GENERATE_TREEVIEW
    vbox->addWidget(r);
    r = new QRadioButton(tr("prepare for compressed HTML (.chm)"));
    m_htmlOptionsGroup->addButton(r, 2);
    // GENERATE_HTMLHELP
    vbox->addWidget(r);
    m_searchEnabled=new QCheckBox(tr("With search function (requires PHP enabled web server)"));
    vbox->addWidget(m_searchEnabled);
    // SEARCH_ENGINE
    m_htmlOptions->setLayout(vbox);
    m_htmlOptions->setChecked(true);
  }
  gbox->addWidget(m_htmlOptions,1,0);

  {
    m_texOptions = new QGroupBox(tr("LaTeX"));
    m_texOptions->setCheckable(true);
    // GENERATE_LATEX
    m_texOptionsGroup = new QButtonGroup(m_texOptions);
    vbox = new QVBoxLayout;
    r = new QRadioButton(tr("as intermediate format for hyperlinked PDF"));
    m_texOptionsGroup->addButton(r, 0);
    // PDF_HYPERLINKS = YES
    r->setChecked(true);
    vbox->addWidget(r);
    r = new QRadioButton(tr("as intermediate format for PDF"));
    m_texOptionsGroup->addButton(r, 1);
    // PDF_HYPERLINKS = NO, USE_PDFLATEX = YES
    vbox->addWidget(r);
    r = new QRadioButton(tr("as intermediate format for PostScript"));
    m_texOptionsGroup->addButton(r, 2);
    // USE_PDFLATEX = NO
    vbox->addWidget(r);
    vbox->addStretch(1);
    m_texOptions->setLayout(vbox);
    m_texOptions->setChecked(true);
  }
  gbox->addWidget(m_texOptions,2,0);

  m_manEnabled=new QCheckBox(tr("Man pages"));
  // GENERATE_MAN
  m_rtfEnabled=new QCheckBox(tr("Rich Text Format (RTF)"));
  // GENERATE_RTF
  m_xmlEnabled=new QCheckBox(tr("XML"));
  // GENERATE_XML
  gbox->addWidget(m_manEnabled,3,0);
  gbox->addWidget(m_rtfEnabled,4,0);
  gbox->addWidget(m_xmlEnabled,5,0);

  gbox->setRowStretch(6,1);
  connect(m_htmlOptions,SIGNAL(toggled(bool)),SLOT(setHtmlEnabled(bool)));
  connect(m_texOptions,SIGNAL(toggled(bool)),SLOT(setLatexEnabled(bool)));
  connect(m_manEnabled,SIGNAL(stateChanged(int)),SLOT(setManEnabled(int)));
  connect(m_rtfEnabled,SIGNAL(stateChanged(int)),SLOT(setRtfEnabled(int)));
  connect(m_xmlEnabled,SIGNAL(stateChanged(int)),SLOT(setXmlEnabled(int)));
  connect(m_searchEnabled,SIGNAL(stateChanged(int)),SLOT(setSearchEnabled(int)));
  connect(m_htmlOptionsGroup,SIGNAL(buttonClicked(int)),
          SLOT(setHtmlOptions(int)));
  connect(m_texOptionsGroup,SIGNAL(buttonClicked(int)),
          SLOT(setLatexOptions(int)));
}

void Step3::setHtmlEnabled(bool b)
{
  updateBoolOption(m_modelData,STR_GENERATE_HTML,b);
}

void Step3::setLatexEnabled(bool b)
{
  updateBoolOption(m_modelData,STR_GENERATE_LATEX,b);
}

void Step3::setManEnabled(int state)
{
  updateBoolOption(m_modelData,STR_GENERATE_MAN,state==Qt::Checked);
}

void Step3::setRtfEnabled(int state)
{
  updateBoolOption(m_modelData,STR_GENERATE_RTF,state==Qt::Checked);
}

void Step3::setXmlEnabled(int state)
{
  updateBoolOption(m_modelData,STR_GENERATE_XML,state==Qt::Checked);
}

void Step3::setSearchEnabled(int state)
{
  updateBoolOption(m_modelData,STR_SEARCHENGINE,state==Qt::Checked);
}

void Step3::setHtmlOptions(int id)
{
  if (id==0) // plain HTML
  {
    updateBoolOption(m_modelData,STR_GENERATE_HTMLHELP,false);
    updateBoolOption(m_modelData,STR_GENERATE_TREEVIEW,false);
  }
  else if (id==1) // with navigation tree
  {
    updateBoolOption(m_modelData,STR_GENERATE_HTMLHELP,false);
    updateBoolOption(m_modelData,STR_GENERATE_TREEVIEW,true);
  }
  else if (id==2) // with compiled help
  {
    updateBoolOption(m_modelData,STR_GENERATE_HTMLHELP,true);
    updateBoolOption(m_modelData,STR_GENERATE_TREEVIEW,false);
  }
}

void Step3::setLatexOptions(int id)
{
  if (id==0) // hyperlinked PDF
  {
    updateBoolOption(m_modelData,STR_USE_PDFLATEX,true);
    updateBoolOption(m_modelData,STR_PDF_HYPERLINKS,true);
  }
  else if (id==1) // PDF
  {
    updateBoolOption(m_modelData,STR_USE_PDFLATEX,true);
    updateBoolOption(m_modelData,STR_PDF_HYPERLINKS,false);
  }
  else if (id==2) // PostScript
  {
    updateBoolOption(m_modelData,STR_USE_PDFLATEX,false);
    updateBoolOption(m_modelData,STR_PDF_HYPERLINKS,false);
  }
}

void Step3::init()
{
  m_htmlOptions->setChecked(getBoolOption(m_modelData,STR_GENERATE_HTML));
  m_texOptions->setChecked(getBoolOption(m_modelData,STR_GENERATE_LATEX));
  m_manEnabled->setChecked(getBoolOption(m_modelData,STR_GENERATE_MAN));
  m_rtfEnabled->setChecked(getBoolOption(m_modelData,STR_GENERATE_RTF));
  m_xmlEnabled->setChecked(getBoolOption(m_modelData,STR_GENERATE_XML));
  m_searchEnabled->setChecked(getBoolOption(m_modelData,STR_SEARCHENGINE));
  if (getBoolOption(m_modelData,STR_GENERATE_HTMLHELP))
  {
    m_htmlOptionsGroup->button(2)->setChecked(true); // compiled help
  }
  else if (getBoolOption(m_modelData,STR_GENERATE_TREEVIEW))
  {
    m_htmlOptionsGroup->button(1)->setChecked(true); // navigation tree
  }
  else
  {
    m_htmlOptionsGroup->button(0)->setChecked(true); // plain HTML
  }
  if (!getBoolOption(m_modelData,STR_USE_PDFLATEX))
  {
    m_texOptionsGroup->button(2)->setChecked(true); // PostScript
  }
  else if (!getBoolOption(m_modelData,STR_PDF_HYPERLINKS))
  {
    m_texOptionsGroup->button(1)->setChecked(true); // Plain PDF
  }
  else
  {
    m_texOptionsGroup->button(0)->setChecked(true); // PDF with hyperlinks
  }
}

//==========================================================================

Step4::Step4(Wizard *wizard,const QHash<QString,Input*> &modelData) 
  : m_wizard(wizard), m_modelData(modelData)
{
  m_diagramModeGroup = new QButtonGroup(this);
  QGridLayout *gbox = new QGridLayout( this );
  gbox->addWidget(new QLabel(tr("Diagrams to generate")),0,0);

  QRadioButton *rb = new QRadioButton(tr("No diagrams"));
  m_diagramModeGroup->addButton(rb, 0);
  gbox->addWidget(rb,1,0);
  // CLASS_DIAGRAMS = NO, HAVE_DOT = NO
  rb->setChecked(true);
  rb = new QRadioButton(tr("Use built-in class diagram generator"));
  m_diagramModeGroup->addButton(rb, 1);
  // CLASS_DIAGRAMS = YES, HAVE_DOT = NO
  gbox->addWidget(rb,2,0);
  rb = new QRadioButton(tr("Use dot tool from the GraphViz package"));
  m_diagramModeGroup->addButton(rb, 2);
  gbox->addWidget(rb,3,0);
  // CLASS_DIAGRAMS = NO, HAVE_DOT = YES

  m_dotGroup = new QGroupBox(tr("Dot graphs to generate"));
    QVBoxLayout *vbox = new QVBoxLayout;
    m_dotClass=new QCheckBox(tr("Class diagrams"));
    // CLASS_GRAPH
    m_dotCollaboration=new QCheckBox(tr("Collaboration diagrams"));
    // COLLABORATION_GRAPH
    m_dotInheritance=new QCheckBox(tr("Overall Class hierarchy"));
    // GRAPHICAL_HIERARCHY
    m_dotInclude=new QCheckBox(tr("Include dependency graphs"));
    // INCLUDE_GRAPH
    m_dotIncludedBy=new QCheckBox(tr("Included by dependency graphs"));
    // INCLUDED_BY_GRAPH
    m_dotCall=new QCheckBox(tr("Call graphs"));
    // CALL_GRAPH
    m_dotCaller=new QCheckBox(tr("Called by graphs"));
    // CALLER_GRAPH
    vbox->addWidget(m_dotClass);
    vbox->addWidget(m_dotCollaboration);
    vbox->addWidget(m_dotInheritance);
    vbox->addWidget(m_dotInclude);
    vbox->addWidget(m_dotIncludedBy);
    vbox->addWidget(m_dotCall);
    vbox->addWidget(m_dotCaller);
    vbox->addStretch(1);
    m_dotGroup->setLayout(vbox);
    m_dotClass->setChecked(true);
    m_dotGroup->setEnabled(false);
  gbox->addWidget(m_dotGroup,4,0);

  m_dotInclude->setChecked(true);
  m_dotCollaboration->setChecked(true);
  gbox->setRowStretch(5,1);

  connect(m_diagramModeGroup,SIGNAL(buttonClicked(int)),
          this,SLOT(diagramModeChanged(int)));
  connect(m_dotClass,SIGNAL(stateChanged(int)),
          this,SLOT(setClassGraphEnabled(int)));
  connect(m_dotCollaboration,SIGNAL(stateChanged(int)),
          this,SLOT(setCollaborationGraphEnabled(int)));
  connect(m_dotInheritance,SIGNAL(stateChanged(int)),
          this,SLOT(setGraphicalHierarchyEnabled(int)));
  connect(m_dotInclude,SIGNAL(stateChanged(int)),
          this,SLOT(setIncludeGraphEnabled(int)));
  connect(m_dotIncludedBy,SIGNAL(stateChanged(int)),
          this,SLOT(setIncludedByGraphEnabled(int)));
  connect(m_dotCall,SIGNAL(stateChanged(int)),
          this,SLOT(setCallGraphEnabled(int)));
  connect(m_dotCaller,SIGNAL(stateChanged(int)),
          this,SLOT(setCallerGraphEnabled(int)));
}

void Step4::diagramModeChanged(int id)
{
  if (id==0) // no diagrams
  {
    updateBoolOption(m_modelData,STR_HAVE_DOT,false);
    updateBoolOption(m_modelData,STR_CLASS_DIAGRAMS,false);
  }
  else if (id==1) // builtin diagrams
  {
    updateBoolOption(m_modelData,STR_HAVE_DOT,false);
    updateBoolOption(m_modelData,STR_CLASS_DIAGRAMS,true);
  }
  else if (id==2) // dot diagrams
  {
    updateBoolOption(m_modelData,STR_HAVE_DOT,true);
    updateBoolOption(m_modelData,STR_CLASS_DIAGRAMS,false);
  }
  m_dotGroup->setEnabled(id==2);
}

void Step4::setClassGraphEnabled(int state)
{
  updateBoolOption(m_modelData,STR_CLASS_GRAPH,state==Qt::Checked);
}

void Step4::setCollaborationGraphEnabled(int state)
{
  updateBoolOption(m_modelData,STR_COLLABORATION_GRAPH,state==Qt::Checked);
}

void Step4::setGraphicalHierarchyEnabled(int state)
{
  updateBoolOption(m_modelData,STR_GRAPHICAL_HIERARCHY,state==Qt::Checked);
}

void Step4::setIncludeGraphEnabled(int state)
{
  updateBoolOption(m_modelData,STR_INCLUDE_GRAPH,state==Qt::Checked);
}

void Step4::setIncludedByGraphEnabled(int state)
{
  updateBoolOption(m_modelData,STR_INCLUDED_BY_GRAPH,state==Qt::Checked);
}

void Step4::setCallGraphEnabled(int state)
{
  updateBoolOption(m_modelData,STR_CALL_GRAPH,state==Qt::Checked);
}

void Step4::setCallerGraphEnabled(int state)
{
  updateBoolOption(m_modelData,STR_CALLER_GRAPH,state==Qt::Checked);
}

void Step4::init()
{
  if (getBoolOption(m_modelData,STR_HAVE_DOT))
  {
    m_diagramModeGroup->button(2)->setChecked(true); // Dot
  }
  else if (getBoolOption(m_modelData,STR_CLASS_DIAGRAMS))
  {
    m_diagramModeGroup->button(1)->setChecked(true); // Builtin diagrams
  }
  else
  {
    m_diagramModeGroup->button(0)->setChecked(true); // no diagrams
  }
  m_dotClass->setChecked(getBoolOption(m_modelData,STR_CLASS_GRAPH));
  m_dotCollaboration->setChecked(getBoolOption(m_modelData,STR_COLLABORATION_GRAPH));
  m_dotInheritance->setChecked(getBoolOption(m_modelData,STR_GRAPHICAL_HIERARCHY));
  m_dotInclude->setChecked(getBoolOption(m_modelData,STR_INCLUDE_GRAPH));
  m_dotIncludedBy->setChecked(getBoolOption(m_modelData,STR_INCLUDED_BY_GRAPH));
  m_dotCall->setChecked(getBoolOption(m_modelData,STR_CALL_GRAPH));
  m_dotCaller->setChecked(getBoolOption(m_modelData,STR_CALLER_GRAPH));
}

//==========================================================================

Wizard::Wizard(const QHash<QString,Input*> &modelData, QWidget *parent) : 
  QSplitter(parent), m_modelData(modelData)
{
  m_treeWidget = new QTreeWidget;
  m_treeWidget->setColumnCount(1);
  m_treeWidget->setHeaderLabels(QStringList() << QString::fromAscii("Topics"));
  QList<QTreeWidgetItem*> items;
  items.append(new QTreeWidgetItem((QTreeWidget*)0,QStringList(tr("Project"))));
  items.append(new QTreeWidgetItem((QTreeWidget*)0,QStringList(tr("Mode"))));
  items.append(new QTreeWidgetItem((QTreeWidget*)0,QStringList(tr("Output"))));
  items.append(new QTreeWidgetItem((QTreeWidget*)0,QStringList(tr("Diagrams"))));
  m_treeWidget->insertTopLevelItems(0,items);

  m_topicStack = new QStackedWidget;
  m_step1 = new Step1(this,modelData);
  m_step2 = new Step2(this,modelData);
  m_step3 = new Step3(this,modelData);
  m_step4 = new Step4(this,modelData);
  m_topicStack->addWidget(m_step1);
  m_topicStack->addWidget(m_step2);
  m_topicStack->addWidget(m_step3);
  m_topicStack->addWidget(m_step4);

  QWidget *rightSide = new QWidget;
  QGridLayout *grid = new QGridLayout(rightSide);
  m_prev = new QPushButton(tr("Previous"));
  m_prev->setEnabled(false);
  m_next = new QPushButton(tr("Next"));
  grid->addWidget(m_topicStack,0,0,1,2);
  grid->addWidget(m_prev,1,0,Qt::AlignLeft);
  grid->addWidget(m_next,1,1,Qt::AlignRight);
  grid->setColumnStretch(0,1);
  grid->setRowStretch(0,1);
  addWidget(m_treeWidget);
  addWidget(rightSide);

  connect(m_treeWidget,
          SIGNAL(currentItemChanged(QTreeWidgetItem *,QTreeWidgetItem *)),
          SLOT(activateTopic(QTreeWidgetItem *,QTreeWidgetItem *)));
  connect(m_next,SIGNAL(clicked()),SLOT(nextTopic()));
  connect(m_prev,SIGNAL(clicked()),SLOT(prevTopic()));

  refresh();
}

Wizard::~Wizard()
{
}

void Wizard::activateTopic(QTreeWidgetItem *item,QTreeWidgetItem *)
{
  if (item)
  {
    
    QString label = item->text(0);
    if (label==tr("Project"))
    {
      m_topicStack->setCurrentWidget(m_step1);
      m_prev->setEnabled(false);
      m_next->setEnabled(true);
    }
    else if (label==tr("Mode"))
    {
      m_topicStack->setCurrentWidget(m_step2);
      m_prev->setEnabled(true);
      m_next->setEnabled(true);
    }
    else if (label==tr("Output"))
    {
      m_topicStack->setCurrentWidget(m_step3);
      m_prev->setEnabled(true);
      m_next->setEnabled(true);
    }
    else if (label==tr("Diagrams"))
    {
      m_topicStack->setCurrentWidget(m_step4);
      m_prev->setEnabled(true);
      m_next->setEnabled(false);
    }
  }
}

void Wizard::nextTopic()
{
  m_topicStack->setCurrentIndex(m_topicStack->currentIndex()+1);
  m_next->setEnabled(m_topicStack->count()!=m_topicStack->currentIndex()+1);
  m_prev->setEnabled(m_topicStack->currentIndex()!=0);
  m_treeWidget->setCurrentItem(m_treeWidget->invisibleRootItem()->child(m_topicStack->currentIndex()));
}

void Wizard::prevTopic()
{
  m_topicStack->setCurrentIndex(m_topicStack->currentIndex()-1);
  m_next->setEnabled(m_topicStack->count()!=m_topicStack->currentIndex()+1);
  m_prev->setEnabled(m_topicStack->currentIndex()!=0);
  m_treeWidget->setCurrentItem(m_treeWidget->invisibleRootItem()->child(m_topicStack->currentIndex()));
}

void Wizard::refresh()
{
  m_step1->init();
  m_step2->init();
  m_step3->init();
  m_step4->init();
}
