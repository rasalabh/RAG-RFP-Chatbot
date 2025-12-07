import os
import glob as file_glob
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document

load_dotenv()

class ImprovedRAGService:
    def __init__(self, data_dir: str = "data", index_dir: str = "faiss_index"):
        self.data_dir = data_dir
        self.index_dir = index_dir
        
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "800"))  # Reduced for better precision
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))
        self.top_k = int(os.getenv("TOP_K_RESULTS", "8"))  # Increased for reranking
        
        print(f"Improved RAG Configuration:")
        print(f"  Chunk Size: {self.chunk_size}")
        print(f"  Chunk Overlap: {self.chunk_overlap}")
        print(f"  Top K Results: {self.top_k}")
        
        # IMPROVEMENT 1: Better embedding model with higher dimensions
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",  # 768-dim vs 384-dim
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}  # Improves similarity search
        )
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
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

    def _chunk_with_page_tracking(self, documents: List[Document], 
                                   chunk_size: int, chunk_overlap: int) -> List[Document]:
        """
        IMPROVEMENT 2: Enhanced chunking that preserves accurate page numbers
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ": ", ", ", " ", ""],
            length_function=len,
            is_separator_regex=False
        )
        
        all_chunks = []
        for doc in documents:
            # Get source file and page info
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", None)
            
            # Split the document
            chunks = text_splitter.split_text(doc.page_content)
            
            # Calculate character position for page tracking
            total_chars = len(doc.page_content)
            
            for i, chunk in enumerate(chunks):
                # Find chunk position in original document
                chunk_start = doc.page_content.find(chunk)
                chunk_position = chunk_start / total_chars if total_chars > 0 else 0
                
                # Create metadata with enhanced info
                chunk_metadata = {
                    "source": source,
                    "page": page if page is not None else "N/A",
                    "chunk_id": i,
                    "chunk_position": chunk_position,
                    "total_chunks": len(chunks),
                    # Add first 100 chars as preview for debugging
                    "preview": chunk[:100].replace("\n", " ")
                }
                
                all_chunks.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))
        
        return all_chunks

    def ingest_folder(self, chunk_size: int = 800, chunk_overlap: int = 150):
        print(f"Scanning {self.data_dir} for documents...")
        
        all_documents = []
        
        # Load PDF files with page tracking
        try:
            pdf_files = file_glob.glob(os.path.join(self.data_dir, "**/*.pdf"), recursive=True)
            for pdf_file in pdf_files:
                try:
                    loader = PyPDFLoader(pdf_file)
                    docs = loader.load()
                    all_documents.extend(docs)
                except Exception as e:
                    print(f"  Error loading {pdf_file}: {e}")
            print(f"  Found {len(pdf_files)} PDF documents")
        except Exception as e:
            print(f"  No PDF files found or error: {e}")
        
        # Load DOCX files (manually add paragraph numbers as "pages")
        try:
            docx_files = file_glob.glob(os.path.join(self.data_dir, "**/*.docx"), recursive=True)
            for docx_file in docx_files:
                try:
                    loader = Docx2txtLoader(docx_file)
                    docs = loader.load()
                    # Split by paragraphs to simulate pages
                    for doc in docs:
                        paragraphs = doc.page_content.split('\n\n')
                        for idx, para in enumerate(paragraphs):
                            if para.strip():
                                all_documents.append(Document(
                                    page_content=para,
                                    metadata={"source": docx_file, "page": f"Para-{idx+1}"}
                                ))
                except Exception as e:
                    print(f"  Error loading {docx_file}: {e}")
            print(f"  Found {len(docx_files)} Word documents")
        except Exception as e:
            print(f"  No Word files found or error: {e}")
        
        # Load XLSX files
        try:
            import openpyxl
            xlsx_files = file_glob.glob(os.path.join(self.data_dir, "**/*.xlsx"), recursive=True)
            for xlsx_file in xlsx_files:
                try:
                    wb = openpyxl.load_workbook(xlsx_file, data_only=True)
                    for sheet_idx, sheet in enumerate(wb.worksheets):
                        text_content = f"Sheet: {sheet.title}\n"
                        for row in sheet.iter_rows(values_only=True):
                            row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                            if row_text.strip():
                                text_content += row_text + "\n"
                        
                        doc = Document(
                            page_content=text_content,
                            metadata={"source": xlsx_file, "page": f"Sheet-{sheet_idx+1}"}
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

        # IMPROVEMENT 3: Use enhanced chunking with page tracking
        texts = self._chunk_with_page_tracking(all_documents, chunk_size, chunk_overlap)

        print(f"Creating embeddings for {len(texts)} chunks...")
        self.vector_store = FAISS.from_documents(texts, self.embeddings)
        
        self.vector_store.save_local(self.index_dir)
        
        return f"Successfully ingested {len(all_documents)} documents and created {len(texts)} chunks (Size: {chunk_size}, Overlap: {chunk_overlap})."

    def _rerank_chunks(self, query: str, chunks: List[Document], top_n: int = 5) -> List[Document]:
        """
        IMPROVEMENT 4: Simple reranking based on keyword matching
        This helps surface chunks that have exact keyword matches
        """
        query_terms = set(query.lower().split())
        
        scored_chunks = []
        for chunk in chunks:
            # Calculate keyword overlap score
            chunk_terms = set(chunk.page_content.lower().split())
            keyword_score = len(query_terms.intersection(chunk_terms)) / len(query_terms)
            
            # Combine with original similarity (chunks are already sorted by similarity)
            # Give 70% weight to original similarity, 30% to keyword matching
            scored_chunks.append((chunk, keyword_score))
        
        # Re-sort by keyword score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N
        return [chunk for chunk, score in scored_chunks[:top_n]]

    def _deduplicate_sources(self, sources: List[Dict]) -> List[Dict]:
        """Remove duplicate source citations"""
        seen = set()
        unique_sources = []
        for source in sources:
            key = (source['file'], source['page'])
            if key not in seen:
                seen.add(key)
                unique_sources.append(source)
        return unique_sources

    def query(self, question: str, top_k: int = 8, temperature: float = 0.7, 
              evaluate: bool = False) -> dict:
        if not self.vector_store:
            return {
                "answer": "Index not found. Please upload documents and ingest them first.",
                "sources": [],
                "contexts": []
            }
        
        # IMPROVEMENT 5: Retrieve more chunks for reranking
        retriever = self.vector_store.as_retriever(search_kwargs={"k": top_k})
        docs = retriever.invoke(question)
        
        # Rerank to get best 5 chunks
        reranked_docs = self._rerank_chunks(question, docs, top_n=5)
        
        # IMPROVEMENT 6: Enhanced context assembly with section markers
        context_parts = []
        for i, doc in enumerate(reranked_docs, 1):
            source_file = doc.metadata.get("source", "Unknown").split('\\')[-1].split('/')[-1]
            page = doc.metadata.get("page", "N/A")
            
            context_parts.append(
                f"[Source {i}: {source_file}, Page {page}]\n{doc.page_content}\n"
            )
        
        context = "\n---\n".join(context_parts)
        contexts_list = [doc.page_content for doc in reranked_docs]
        
        # Extract sources with deduplication
        sources = []
        for doc in reranked_docs:
            source_info = {
                "file": doc.metadata.get("source", "Unknown").split('\\')[-1].split('/')[-1],
                "page": doc.metadata.get("page", "N/A"),
                "preview": doc.metadata.get("preview", "")[:100]
            }
            sources.append(source_info)
        
        sources = self._deduplicate_sources(sources)
        
        # IMPROVEMENT 7: Enhanced prompt with reasoning and citation instructions
        prompt_text = f"""You are a helpful AI assistant analyzing documents. Answer the question using ONLY the provided context sources.

INSTRUCTIONS:
1. Read all context sources carefully
2. Think step-by-step about how to answer the question
3. Cite specific sources when making claims (e.g., "According to Source 1...")
4. If the answer requires information from multiple sources, synthesize them
5. If the context doesn't contain enough information, say "The provided documents don't contain sufficient information to answer this question."
6. Be precise and factual - do not add information not in the context

CONTEXT SOURCES:
{context}

QUESTION: {question}

REASONING PROCESS:
Let me analyze this step by step:
1. What is the question asking?
2. Which sources contain relevant information?
3. What is the answer based on these sources?

ANSWER (with source citations):"""
        
        # Create LLM with dynamic temperature
        dynamic_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=temperature
        )
        
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