import os
import glob as file_glob
from typing import List
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document

load_dotenv()

class RAGService:
    def __init__(self, data_dir: str = "data", index_dir: str = "faiss_index"):
        self.data_dir = data_dir
        self.index_dir = index_dir
        
        # Configurable chunk settings (optimized for RFP documents)
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))  # Optimized for all-MiniLM-L6-v2
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))  #  20% overlap
        self.top_k = int(os.getenv("TOP_K_RESULTS", "5"))  # Retrieve 5 chunks
        
        # Log configuration for verification
        print(f"RAG Configuration:")
        print(f"  Chunk Size: {self.chunk_size}")
        print(f"  Chunk Overlap: {self.chunk_overlap}")
        print(f"  Top K Results: {self.top_k}")
        
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
        self.vector_store = None
        self._load_index_if_exists()

    def _load_index_if_exists(self):
        if os.path.exists(self.index_dir):
            try:
                self.vector_store = FAISS.load_local(
                    self.index_dir, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"Loaded existing FAISS index from {self.index_dir}")
            except Exception as e:
                print(f"Could not load index: {e}")

    def ingest_folder(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        print(f"Scanning {self.data_dir} for documents...")
        
        # Load different file types
        all_documents = []
        
        # Load PDF files
        try:
            pdf_loader = DirectoryLoader(
                self.data_dir, 
                glob="**/*.pdf", 
                loader_cls=PyPDFLoader
            )
            pdf_docs = pdf_loader.load()
            all_documents.extend(pdf_docs)
            print(f"  Found {len(pdf_docs)} PDF documents")
        except Exception as e:
            print(f"  No PDF files found or error: {e}")
        
        # Load Word (.docx) files
        try:
            docx_files = file_glob.glob(os.path.join(self.data_dir, "**/*.docx"), recursive=True)
            for docx_file in docx_files:
                try:
                    loader = Docx2txtLoader(docx_file)
                    docs = loader.load()
                    all_documents.extend(docs)
                except Exception as e:
                    print(f"  Error loading {docx_file}: {e}")
            print(f"  Found {len(docx_files)} Word documents")
        except Exception as e:
            print(f"  No Word files found or error: {e}")
        
        # Load Excel (.xlsx) files
        try:
            import openpyxl
            xlsx_files = file_glob.glob(os.path.join(self.data_dir, "**/*.xlsx"), recursive=True)
            for xlsx_file in xlsx_files:
                try:
                    wb = openpyxl.load_workbook(xlsx_file, data_only=True)
                    text_content = ""
                    for sheet in wb.worksheets:
                        text_content += f"\n\nSheet: {sheet.title}\n"
                        for row in sheet.iter_rows(values_only=True):
                            row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                            if row_text.strip():
                                text_content += row_text + "\n"
                    
                    doc = Document(
                        page_content=text_content,
                        metadata={"source": xlsx_file}
                    )
                    all_documents.append(doc)
                except Exception as e:
                    print(f"  Error loading {xlsx_file}: {e}")
            print(f"  Found {len(xlsx_files)} Excel documents")
        except Exception as e:
            print(f"  No Excel files found or error: {e}")
        
        if not all_documents:
            return "No documents found in data directory."

        print(f"\nTotal documents loaded: {len(all_documents)}")

        # Optimized separators for RFP documents (structured content)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",  # Double newline (paragraphs)
                "\n",    # Single newline
                ". ",    # Sentences
                ", ",    # Clauses
                " ",     # Words
                ""       # Characters (fallback)
            ],
            length_function=len
        )
        texts = text_splitter.split_documents(all_documents)

        print(f"Creating embeddings for {len(texts)} chunks...")
        self.vector_store = FAISS.from_documents(texts, self.embeddings)
        
        self.vector_store.save_local(self.index_dir)
        
        # Count files by type
        pdf_count = len([d for d in all_documents if d.metadata.get("source", "").endswith(".pdf")])
        docx_count = len([d for d in all_documents if d.metadata.get("source", "").endswith(".docx")])
        xlsx_count = len([d for d in all_documents if d.metadata.get("source", "").endswith(".xlsx")])
        
        file_summary = []
        if pdf_count > 0:
            file_summary.append(f"{pdf_count} PDF")
        if docx_count > 0:
            file_summary.append(f"{docx_count} Word")
        if xlsx_count > 0:
            file_summary.append(f"{xlsx_count} Excel")
        
        return f"Successfully ingested {len(all_documents)} documents ({', '.join(file_summary)}) and created {len(texts)} chunks (Size: {chunk_size}, Overlap: {chunk_overlap})."

    def query(self, question: str, top_k: int = 5, temperature: float = 0.7, evaluate: bool = False) -> dict:
        if not self.vector_store:
            return {
                "answer": "Index not found. Please upload documents and ingest them first.",
                "sources": [],
                "contexts": []
            }
        
        retriever = self.vector_store.as_retriever(search_kwargs={"k": top_k})
        
        # Get context documents
        docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])
        contexts_list = [doc.page_content for doc in docs]  # For evaluation
        
        # Extract sources
        sources = []
        for doc in docs:
            source_info = {
                "file": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", "N/A")
            }
            if source_info not in sources:
                sources.append(source_info)
        
        # Create prompt
        prompt_text = f"""Answer the question as precise as possible using the provided context. If the answer is not contained in the context, say "answer not available in context"

Context:
{context}

Question: {question}

Answer:"""
        
        # Create LLM with dynamic temperature
        dynamic_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=temperature
        )
        
        # Use LLM to generate answer
        response = dynamic_llm.invoke(prompt_text)
        
        result = {
            "answer": response.content,
            "sources": sources,
            "contexts": contexts_list if evaluate else []
        }
        
        # Run evaluation if requested
        if evaluate:
            from rag_evaluator import RAGEvaluator
            evaluator = RAGEvaluator()
            evaluation = evaluator.comprehensive_evaluation(
                query=question,
                answer=response.content,
                contexts=contexts_list,
                sources=sources
            )
            result["evaluation"] = evaluation
        
        return result
