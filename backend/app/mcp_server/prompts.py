from app.mcp_server.server import mcp_server
from app.observability.logging import logger

@mcp_server.prompt("architecture_review")
def prompt_architecture_review(repo_name: str) -> str:
    """
    Standard review template to scan a repository's architecture, layers, and entry points.
    """
    logger.info("MCP Prompt 'architecture_review' requested")
    return (
        f"Hãy phân tích kiến trúc tổng quan của repository '{repo_name}'.\n"
        "Đặc biệt làm rõ:\n"
        "1. Cấu trúc các thư mục chính và phân lớp (API layer, Agent layer, RAG database, v.v.).\n"
        "2. Điểm bắt đầu (Entry points) của ứng dụng nằm ở đâu?\n"
        "3. Các file cấu hình deploy (Docker, Compose, Makefile) hoạt động thế nào?\n"
        "4. Đánh giá xem kiến trúc này có ưu/nhược điểm gì trong môi trường production."
    )

@mcp_server.prompt("rag_answer_with_citations")
def prompt_rag_answer_with_citations(query: str) -> str:
    """
    Forces the agentic engine to respond grounded in context with detailed source-level citations.
    """
    logger.info("MCP Prompt 'rag_answer_with_citations' requested")
    return (
        f"Hãy trả lời câu hỏi sau của người dùng dựa trên tài liệu tham khảo: '{query}'.\n"
        "Yêu cầu:\n"
        "- Trích dẫn rõ số thứ tự nguồn dạng [1], [2] tương ứng.\n"
        "- Nếu thông tin trong tài liệu tham khảo không đủ, hãy trả lời chính xác: 'Không tìm thấy đủ bằng chứng trong tài liệu đã ingest.'\n"
        "- Tuyệt đối không bịa đặt số liệu hay thông tin không có trong tài liệu."
    )

@mcp_server.prompt("code_review")
def prompt_code_review(module_name: str) -> str:
    """
    Inspects specific directories or files, detecting safety risks, missing retries, or testing gaps.
    """
    logger.info("MCP Prompt 'code_review' requested")
    return (
        f"Hãy tiến hành review chi tiết module '{module_name}' trong dự án.\n"
        "Tập trung phân tích các khía cạnh:\n"
        "- Các lỗi bảo mật (Security flaws) hoặc lỗi validation đầu vào.\n"
        "- Khả năng chịu lỗi: Đã có cơ chế retry khi gọi API ngoài (như embedding, LLM) chưa?\n"
        "- Cấu trúc mã nguồn: Đã tách nhỏ các class/function độc lập chưa?\n"
        "- Kiểm thử: Đã có unit test bao phủ các luồng chính chưa?\n\n"
        "Hãy liệt kê kết quả và phân loại việc cần làm theo các mức ưu tiên: P0 (Khẩn cấp), P1 (Nên có), P2 (Cải tiến nhỏ)."
    )

@mcp_server.prompt("task_breakdown")
def prompt_task_breakdown(goal: str) -> str:
    """
    Standard planning prompt to decompose engineering objectives into structured checklists.
    """
    logger.info("MCP Prompt 'task_breakdown' requested")
    return (
        f"Hãy phân rã mục tiêu kỹ thuật sau đây thành một roadmap checklist triển khai cụ thể: '{goal}'.\n"
        "Yêu cầu đầu ra:\n"
        "1. Chia theo tiến trình thời gian hợp lý (ví dụ: Day 1, Day 2, hoặc Step 1, Step 2).\n"
        "2. Mỗi đầu việc cần có tiêu đề rõ ràng, mô tả ngắn gọn và gán nhãn ưu tiên (P0, P1, P2).\n"
        "3. Định dạng đầu ra dạng Markdown danh sách checklist: - [ ] Tiêu đề việc cần làm."
    )
