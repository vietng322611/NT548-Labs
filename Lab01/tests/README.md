# Kiểm thử Lab01 bằng Python

Sáu module dùng chung cho Terraform/CloudFormation, chỉ đọc cấu hình AWS và thử SSH; không deploy/destroy.

## Chuẩn bị

- Có Python 3.10+ và AWS CLI trên máy chạy test; không cần cài gói pip hoặc jq.
- Cấu hình credentials AWS cho terminal chạy test, đúng tài khoản/region và có quyền đọc tài nguyên Lab01. Nếu dùng profile, đặt `AWS_PROFILE`.
- Triển khai tài nguyên cần kiểm thử và đợi tài nguyên sẵn sàng.
- Cấu hình kỳ vọng: VPC `10.0.0.0/16`, public/private subnet `10.0.1.0/24` và `10.0.2.0/24`, AZ `us-east-1a`.

### Thư mục và terminal

- Các ví dụ dùng **cú pháp Bash**. Nếu dùng PowerShell, cần đổi cú pháp biến, đường dẫn và nối dòng tương ứng; dùng `python` hoặc `py -3` thay `python3` nếu đó là lệnh Python 3.10+ trên máy.
- Thư mục hiện tại phải chứa `Lab01/tests`, không phải thư mục chứa README. Kiểm tra bằng `ls Lab01/tests`.
- Khai báo biến và chạy test trong **cùng terminal**. Không chạy trực tiếp file Python trong `tests`.

```bash
aws sts get-caller-identity
REGION='us-east-1'
```

### Lấy thông số

Chọn nguồn tương ứng với công cụ đã triển khai:

| Biến | Terraform | CloudFormation |
| --- | --- | --- |
| `VPC_ID` | Output `vpc_id` | Output `VpcId` |
| `PUBLIC_IP` | Output `public_ec2_ip` | Output `PublicEc2Ip` |
| `PRIVATE_IP` | Output `private_ec2_ip` | Output `PrivateEc2Ip` |
| `NAT_IP` | Chưa có root output; lấy từ AWS Console hoặc AWS CLI | Output `NatElasticIp` |

**Terraform:** chạy các lệnh sau từ thư mục chứa `Lab01`, với state của lần triển khai cần kiểm thử. Terraform phải có trong `PATH` của terminal.

```bash
VPC_ID=$(terraform -chdir=Lab01/terraform output -raw vpc_id)
PUBLIC_IP=$(terraform -chdir=Lab01/terraform output -raw public_ec2_ip)
PRIVATE_IP=$(terraform -chdir=Lab01/terraform output -raw private_ec2_ip)
```

Lấy `NAT_IP` trên AWS Console: chọn đúng region, mở **VPC → NAT gateways**, lọc theo `VPC_ID`, chọn NAT đang `Available`, sao chép **Public IPv4 address**. Hoặc dùng AWS CLI:

```bash
aws ec2 describe-nat-gateways --region "$REGION" \
  --filter "Name=vpc-id,Values=$VPC_ID" "Name=state,Values=available" \
  --query 'NatGateways[].NatGatewayAddresses[].PublicIp' --output text
```

**CloudFormation:** chọn đúng region trên AWS Console, mở **CloudFormation → Stacks → stack gốc đã triển khai → Outputs**. Sao chép giá trị theo bảng trên, không chọn nested stack.

Gán các giá trị lấy từ Console vào biến; nếu đã lấy bằng Terraform thì chỉ cần gán `NAT_IP`:

```bash
VPC_ID='vpc-THAY_BANG_ID_THUC_TE'
PUBLIC_IP='PUBLIC_IPV4_THUC_TE'
PRIVATE_IP='PRIVATE_IPV4_THUC_TE'
NAT_IP='NAT_ELASTIC_IP_THUC_TE'
SSH_CIDR='IP_QUAN_TRI_THUC_TE/32'
```

`SSH_CIDR` là **IPv4 public của mạng đang dùng để SSH**, kèm `/32`; không phải IP LAN hoặc IP EC2. Giá trị phải khớp CIDR quản trị đã cấu hình khi triển khai. Đổi mạng hoặc bật VPN có thể làm IP nguồn thay đổi; cần cập nhật cấu hình quản trị trước khi kiểm thử SSH.

### Private key và cấu hình cố định

- Kiểm thử SSH cần private key tương ứng với key pair đã cấu hình trên cả hai EC2. File phải có trên máy chạy test và đọc được từ terminal; file `.pub` không thay thế được private key. Đặt đường dẫn file vào `PRIVATE_KEY` ở mục SSH.
- Test dùng CIDR và AZ cố định nêu ở mục Chuẩn bị. Hạ tầng dùng giá trị khác có thể báo `FAIL` dù vẫn hoạt động; cần đối chiếu và sửa kỳ vọng trong test nếu chủ động đổi cấu hình. Thay `REGION` **không tự thay đổi AZ kỳ vọng**.

## Điều kiện và kết quả kỳ vọng

| Module | Điều kiện trước khi chạy | Kết quả kỳ vọng |
| --- | --- | --- |
| Network | Đã tạo VPC, subnet, IGW | VPC/subnet `available`, DNS bật; đúng CIDR/AZ; public bật auto public IPv4, private tắt; IGW gắn VPC, SG `default` tồn tại. |
| Routing | Mỗi subnet đã liên kết tường minh với route table | Local route active, public default route tới IGW; `before-nat`: private chưa có default route; `after-nat`: private default route active tới NAT available. |
| NAT | NAT `available`, EIP đã gắn | Đúng một NAT available trong VPC, loại public, nằm trong public subnet; IP và interface khớp EIP. |
| Compute | Mỗi subnet có một EC2, đợi status checks đạt | EC2 `running`, `t3.micro`, Amazon Linux 2023, key pair tồn tại; root `gp3` 8 GiB, tự xóa khi terminate; hai status checks `ok`; chỉ public EC2 có public IPv4. |
| Security | Hai EC2 running, mỗi máy gắn một SG riêng; biết CIDR quản trị | Hai SG custom khác nhau; mỗi SG chỉ một inbound TCP 22: public từ CIDR quản trị, private từ public SG; outbound cho phép mọi IPv4. |
| SSH | Năm module trên đều PASS khi kiểm tra hạ tầng sau NAT; có OpenSSH, private key đúng đã nạp vào agent; nguồn SSH thuộc CIDR cho phép | SSH public và private qua public thành công; private truy cập Internet với IP nguồn đúng NAT EIP. |

## 1. Network

```bash
python3 -m Lab01.tests.test_vpc "$VPC_ID" "$REGION"
```

## 2. Routing

Chọn đúng giai đoạn hạ tầng; `after-nat` là mặc định. Không chạy `before-nat` khi private đã có default route tới NAT.

```bash
# Trước khi thêm NAT và private default route:
python3 -m Lab01.tests.test_routing "$VPC_ID" "$REGION" before-nat
# Sau khi NAT available và private default route đã tạo:
python3 -m Lab01.tests.test_routing "$VPC_ID" "$REGION" after-nat
```

## 3. NAT

```bash
python3 -m Lab01.tests.test_nat "$VPC_ID" "$REGION"
```

## 4. Compute

```bash
python3 -m Lab01.tests.test_compute "$VPC_ID" "$REGION"
```

## 5. Security

```bash
python3 -m Lab01.tests.test_security "$VPC_ID" "$SSH_CIDR" "$REGION"
```

## 6. SSH

Public EC2 cần cho phép TCP forwarding cho ProxyJump; private EC2 cần `curl` và kết nối HTTPS. Dùng user `ec2-user` và cùng key cho hai máy.

Dùng các biến IP đã lấy ở mục Lấy thông số. Thay đường dẫn ví dụ bằng private key thực tế:

```bash
PRIVATE_KEY="$HOME/.ssh/ten-private-key"
chmod 600 "$PRIVATE_KEY"
# Trong Bash, chạy nếu chưa có SSH agent:
eval "$(ssh-agent -s)"
ssh-add "$PRIVATE_KEY"
python3 -m Lab01.tests.test_ssh "$PUBLIC_IP" "$PRIVATE_IP" "$NAT_IP" "$PRIVATE_KEY"
```

Nhập passphrase trực tiếp trong terminal khi `ssh-add` hỏi. Giữ private key cục bộ, không chép lên EC2; agent forwarding bị tắt. Script không hỏi passphrase.

Host mới được lưu vào `known_hosts` theo `accept-new`; hãy đối chiếu fingerprint qua kênh tin cậy trước khi kết nối lần đầu. Host đã biết đổi key sẽ bị từ chối; không tắt xác minh host key để vượt lỗi.

## Đọc kết quả

- `PASS` cho từng kiểm tra đạt; exit code `0` nghĩa là toàn bộ kiểm tra của module đạt.
- Module **dừng ở lỗi đầu tiên**. Exit code `1` nghĩa là kiểm tra thất bại, thiếu tài nguyên hoặc lỗi AWS/SSH/timeout; không có nghĩa các kiểm tra phía sau đã chạy.
- Exit code `2`: sai/thiếu tham số CLI hoặc stage không hợp lệ, kèm hướng dẫn usage.
- Chạy riêng từng module; không dùng unittest discovery thay cho các lệnh trên.

## Lỗi thường gặp

| Lỗi | Cần kiểm tra |
| --- | --- |
| `No module named Lab01` | Chạy từ thư mục chứa `Lab01`. |
| Không tìm thấy `aws`, `python3`, `ssh` hoặc `ssh-add` | Kiểm tra công cụ đã cài và có trong `PATH` của terminal; tên lệnh Python có thể là `python` hoặc `py -3`. |
| Credentials hết hạn hoặc `AccessDenied` | Tài khoản, profile, phiên đăng nhập và quyền đọc tài nguyên. |
| SSH timeout | Public IP, CIDR quản trị, route và trạng thái EC2. |
| `Permission denied (publickey)` | Private key, user `ec2-user` và key đã nạp vào agent. |
| Host key thay đổi | Xác minh fingerprint qua kênh tin cậy; không tắt xác minh để vượt lỗi. |
