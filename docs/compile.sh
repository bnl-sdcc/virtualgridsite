#!/bin/bash

echo "compiling LaTeX..."

f_download_template(){
    wget -N http://cms.iopscience.iop.org/alfresco/d/d/workspace/SpacesStore/a83f1ab6-cd8f-11e0-be51-5d01ae4695ed/LaTeXTemplates.zip
    unzip LaTeXTemplates.zip
}

f_donload_src(){
    wget -N https://raw.githubusercontent.com/jose-caballero/virtualgridsite/master/docs/chep2016.tex
    wget -N https://raw.githubusercontent.com/jose-caballero/virtualgridsite/master/docs/chep2016.bbl
}

f_download_images(){
    mkdir images 2>/dev/null
    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/uml/virtualgridsite/opportunistic.png
    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/uml/virtualgridsite/dedicated.png
    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/uml/virtualgridsite/opportunistic_custom.png
    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/uml/virtualgridsite/dedicated_custom.png

    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/figures/virtualgridsite/snippet1.png
    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/figures/virtualgridsite/snippet2.png
    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/figures/virtualgridsite/snippet3.png
    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/figures/virtualgridsite/snippet4.png
    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/figures/virtualgridsite/snippet5.png
    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/figures/virtualgridsite/snippet6.png

    wget -P images -N http://www.usatlas.bnl.gov/~caballer/files/figures/virtualgridsite/newfloat.sty

}

f_pdflatex(){
    #  twice, to compile the cross references
    pdflatex chep2016.tex
    pdflatex chep2016.tex
}

f_latex(){
    latex chep2016.tex
}

f_dvips(){
    dvips -Ppdf -G0 -ta4 chep2016.dvi 
}

f_ps2pdf(){
    ps2pdf -dMaxSubsetPct=100 -dCompatibilityLevel=1.4 -dSubsetFonts=true -dEmbedAllFonts=true -sPAPERSIZE=a4 chep2016.ps
}

f_cleanup(){
    rm -f chep2016.aux
    rm -f chep2016.dvi
    rm -f chep2016.log
    rm -f chep2016.ps
}

# -----------------------------------------------------------------------------

f_download_template
if [ $? -ne 0 ]; then
    exit 
fi

f_donload_src
if [ $? -ne 0 ]; then
    exit 
fi

f_download_images
if [ $? -ne 0 ]; then
    exit 
fi

#f_latex
#if [ $? -ne 0 ]; then
#    exit 
#fi
#f_dvips
#if [ $? -ne 0 ]; then
#    exit 
#fi
#f_ps2pdf
#if [ $? -ne 0 ]; then
#    exit 
#fi

f_pdflatex
if [ $? -ne 0 ]; then
    exit 
fi


f_cleanup
if [ $? -ne 0 ]; then
    exit 
fi
