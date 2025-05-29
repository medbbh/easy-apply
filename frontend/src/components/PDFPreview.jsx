import { useState } from 'react'
import { Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton, Box } from '@chakra-ui/react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

const PDFPreview = ({ isOpen, onClose, pdfUrl }) => {
  const [numPages, setNumPages] = useState(null)
  const [pageNumber, setPageNumber] = useState(1)

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages)
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent maxW="90vw" maxH="90vh">
        <ModalHeader>Document Preview</ModalHeader>
        <ModalCloseButton />
        <ModalBody overflow="auto">
          <Box display="flex" justifyContent="center" alignItems="center">
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={<LoadingSpinner />}
            >
              <Page
                pageNumber={pageNumber}
                width={Math.min(window.innerWidth * 0.8, 800)}
                renderTextLayer={false}
                renderAnnotationLayer={false}
              />
            </Document>
          </Box>
        </ModalBody>
      </ModalContent>
    </Modal>
  )
}

export default PDFPreview 