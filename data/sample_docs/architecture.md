# Kiến Trúc Hệ Thống NT533: Autoscaling & Monitoring

Tài liệu này đặc tả cơ chế tự động mở rộng quy mô (Autoscaling) và giám sát (Monitoring) của hệ thống trong môi trường K3s Kubernetes.

## 1. Cơ Chế Autoscaling (Tự Động Mở Rộng Quy Mô)
Hệ thống sử dụng **Prometheus** làm công cụ chính để thu thập các metrics thời gian thực (real-time metrics) của các thành phần, bao gồm tải CPU, dung lượng Memory, và tần suất request của các OpenFaaS function pods.

Quy trình kích hoạt HPA (Horizontal Pod Autoscaler):
1. **Prometheus** thu thập số liệu metric tải của hệ thống cứ sau mỗi 15 giây.
2. Bộ điều phối **Horizontal Pod Autoscaler (HPA)** truy vấn số liệu metric CPU/Memory từ Prometheus thông qua Kubernetes Metrics Server.
3. Khi ngưỡng CPU vượt quá **75%**, HPA tự động tính toán số lượng bản sao (replica count) cần thiết.
4. HPA gửi lệnh scale tới OpenFaaS gateway để mở rộng số lượng pod phục vụ function pods lên tối đa 10 replicas nhằm giảm tải ngay lập tức.

## 2. Ảnh Hưởng Của Độ Trễ Mạng (Network Latency)
Trong mô hình cụm biên K3s cluster, độ trễ mạng có thể tác động trực tiếp đến thời gian phản hồi (response time) của HPA. Để khắc phục, hệ thống áp dụng cơ chế cooling-down period (thời gian làm nguội) là **180 giây** trước khi thực hiện hành vi scale-in (thu hẹp) để tránh hiện tượng dập dình (thrashing).

---
*Tài liệu kỹ thuật lưu hành nội bộ NT533 - Cập nhật 2026*
