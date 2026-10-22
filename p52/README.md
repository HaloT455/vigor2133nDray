# ALICE P52 — trang LAN 192.168.4.210, sửa chức năng từ P51

Ngày: 22/10/2026. Giữ giao diện, CSS, logo và BIN của đúng bản P51 người dùng cung cấp. Không bật VLAN, không đổi LAN2 hoặc IP quản trị DrayTek.

| Mục | Địa chỉ / điều kiện |
| --- | --- |
| Quản trị modem | http://192.168.4.1 |
| Chat Alice trên các thiết bị LAN | http://192.168.4.210 |
| Máy thực sự chạy Gateway/AI | X270/Linux, phải bật và nối trực tiếp vào LAN 192.168.4.x |
| Điều khiển cấu hình modem | Trang Alice trong phiên quản trị DrayOS, dùng form gốc và đọc lại |
| Số liệu modem | Phiên quản trị đọc dashboard/Data Flow rồi đồng bộ; hết hạn sau 180 giây |

## Cài trang .4.210 trên X270 (không cần nạp firmware để có trang Gateway)

1. Giải nén `ALICE_P52_LAN210_GATEWAY.zip` trong Downloads.
2. Kết nối X270 với Wi-Fi/LAN DrayTek. `ip -4 route get 192.168.4.1` phải có `src 192.168.4.x`, không qua gateway 192.168.2.1.
3. Chạy:

```bash
cd ~/Downloads/ALICE_P52_LAN210
sudo python3 install_lan210.py
```

Nếu thiếu công cụ, chạy lệnh gói cài hiển thị (`sudo apt install nginx network-manager iputils-arping`) rồi chạy lại. Có thể kiểm tra trước bằng `sudo python3 install_lan210.py --check`.

Gói cài kiểm tra trùng IP, thêm địa chỉ phụ cố định `192.168.4.210/24` vào đúng profile NetworkManager, không đổi IP DHCP/gateway/DNS hiện có. Dịch vụ mới `alice-p52` nghe loopback 8210; Nginx phục vụ cổng 80 cho LAN 192.168.4.0/24. Giữ dịch vụ Gateway cũ; khôi phục phần thay đổi mới nếu kiểm tra thất bại. Không mở quản trị WAN hay tắt firewall.

Dành riêng **192.168.4.210** trên DHCP router để không cấp cho máy khác. Điện thoại/PC phải cùng LAN này; Wi-Fi khách, AP/client isolation hoặc subnet khác có thể chặn truy cập. Hai mesh dùng AP/bridge cùng LAN khi cần cùng truy cập. X270 phải tiếp tục bật; địa chỉ này thuộc X270, không phải IP ảo tự tạo trong BIN modem.

Kiểm tra trên X270 rồi trên một thiết bị khác:

```bash
curl --noproxy '*' --connect-timeout 3 http://192.168.4.210/alice-api/health
```

Trên điện thoại mở **http://192.168.4.210**. Dùng HTTP đúng như địa chỉ trên. Nếu trình duyệt router đang dùng HTTPS và chặn gọi Gateway HTTP, mở trang Gateway ở tab riêng.

## Bật mô hình hội thoại

Bifrost và OmniRoute là Gateway định tuyến tới mô hình; chúng không tự chứa mô hình sinh ngôn ngữ. P52 dùng Python stdlib để triển khai độc lập các mẫu định tuyến phù hợp: phân loại lỗi, chuyển nguồn, tạm ngưng nguồn lỗi, Retry-After, giới hạn tổng thời gian, xếp ưu tiên/tải/độ trễ và hạn mức từng lần gọi. Không nhét dịch vụ Go/Node hoặc trọng số LLM vào ROM.

- Các provider có sẵn trong `providers.example.json` **đang tắt**, URL/cổng và tên model chỉ là ví dụ. Sửa `/etc/alice-gateway/routes.json` theo Gateway/model đang chạy thật. Hỗ trợ OpenAI-compatible `/v1/chat/completions`.
- Có thể dùng Bifrost hoặc OmniRoute đang chạy trên X270 làm upstream; lấy đúng URL và model từ cài đặt của chúng.
- Provider HTTPS ngoài máy phải được cho phép rõ trong `ALICE_REMOTE_HOST_ALLOWLIST`; khóa chỉ nằm trong biến môi trường `ALICE_*`, không vào ROM/trình duyệt.
- Installer giữ routes hiện có. Tự đọc các env-file hiện có `/etc/alice-gateway.env`, `/etc/alice-gateway/gateway.env`, `/etc/alice-gateway/.env`. Nếu khóa nằm trong file khác, thêm `--env-file /đường/dẫn/file.env` khi cài.
- Đổi routes hoặc env xong chạy `sudo systemctl restart alice-p52`.
- Trang báo riêng "đã cấu hình" và "đã có phản hồi mô hình". Khi chưa có model, chat trả lời tư vấn theo quy tắc Offline, không tự nhận là ChatGPT.
- Chat nhớ 12 lượt trong tab, đưa CPU/RAM/cấu hình/lưu lượng hợp lệ vào ngữ cảnh. Không đưa IP thiết bị, token hoặc HTML quản trị vào prompt.

Tham khảo thiết kế: [Bifrost](https://github.com/maximhq/bifrost), [OmniRoute](https://github.com/cheaper-inference/OmniRoute). Không sao chép mã nguồn hai dự án vào bản này.

## Sửa trang modem trong firmware

- Nhúng các script lõi của Alice vào chính 2 trang HTML để giảm phụ thuộc tải/cache file JS; khôi phục token từ phiên quản trị cùng nguồn.
- Dùng địa chỉ Gateway mặc định `.4.210`, chuyển cấu hình địa chỉ cũ `.2.210`, `.4.145`, `.10.1` sang mặc định mới; vẫn cho nhập Gateway khác.
- Đọc dashboard JSON; có phương án đọc CPU/RAM số trực tiếp trong HTML dashboard khi CGI JSON lỗi. Không thực thi HTML/script trả về để lấy số liệu.
- Bảng thống kê lấy đối tượng số liệu thật, giữ giá trị 0%, hiển thị thời điểm đo, bỏ số liệu quá 180 giây; phiên/số thiết bị chưa đọc được hiển thị chưa có.
- Auto-Adjustment có bật/tắt/khôi phục qua form DrayOS gốc; giữ giới hạn/quy tắc còn lại và chỉ báo thành công khi đọc lại khớp.
- Gateway ở `.4.210` phục vụ chat cho LAN; thao tác quản trị vẫn phải vào phiên admin tại `.4.1`. Gateway không tự đăng nhập hay tự sửa WAN/DHCP/VLAN.

## Build và kiểm thử mã nguồn

Mã nguồn trong thư mục `p52` trên nhánh GitHub. Firmware gốc và các tài nguyên DrayTek không được đưa lên kho công khai.

```bash
python3 -m unittest discover -s tests -v
node tests/frontend.cjs
python3 tools/build_p52.py /path/to/P51.all --output /path/to/P52.all
```

Builder cần liblz4 của hệ thống và kiểm tra SHA256 chính xác P51: `717addfa8655055efe3d9df03cd6e69f1c2ea894642b470de00f66cd4f9a8f24`. Từ chối baseline khác, giới hạn cứng 27.000.000 byte, kiểm tra lại mọi tài nguyên/BIN/WEB/MD5. Script test trình duyệt riêng cần fixture/tài nguyên OEM riêng, không phát hành công khai.

## Giới hạn đã biết

Các kiểm thử chạy trên máy phát triển và fixture OEM; chưa chạy installer trên X270 nhà bạn, chưa xác minh truy cập từ điện thoại và chưa boot/flash bản P52 trên Vigor2133n. BIN P51 giữ nguyên; bản này không thêm server HTTP/LLM tự chạy trong RTOS. Còn dung lượng ROM không thay thế được RAM/CPU hoặc một model đang chạy. Không chèn dữ liệu rỗng/thư viện không dùng để làm đầy 27 MB.

Kiểm thử có mô hình giả lập không chứng minh chất lượng câu trả lời của model thực. Cân bằng/tận dụng hết băng thông ISP cần số đo WAN, thiết bị và độ trễ thực; bản này không khẳng định đã tự điều tiết toàn hệ thống.
