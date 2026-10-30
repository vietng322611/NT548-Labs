# NT548 Lab01 - Terraform

Triển khai hạ tầng AWS bằng Terraform, gồm VPC, Public Subnet, Private Subnet, Internet Gateway, NAT Gateway, Route Tables, hai EC2 instance và Security Groups.

Hướng dẫn dưới đây sử dụng Ubuntu/WSL. Chạy các lệnh trong cùng terminal.

## 1. Hạ tầng triển khai

| Thành phần | Cấu hình |
| --- | --- |
| Region | `us-east-1` |
| VPC | `10.0.0.0/16` |
| Public Subnet | `10.0.1.0/24`, Availability Zone `us-east-1a` |
| Private Subnet | `10.0.2.0/24`, Availability Zone `us-east-1a` |
| Public Route Table | Route `0.0.0.0/0` đến Internet Gateway |
| Private Route Table | Route `0.0.0.0/0` đến NAT Gateway |
| NAT Gateway | Đặt trong Public Subnet, được gán Elastic IP |
| EC2 | Hai instance Amazon Linux 2023, `t3.micro`, ổ đĩa `gp3` 8 GiB |
| Public EC2 | Có Public IPv4; cho phép SSH từ IP người dùng `/32` |
| Private EC2 | Không có Public IPv4; cho phép SSH từ Public EC2 Security Group |
| Default Security Group | Không có inbound hoặc outbound rule |

Hai Security Groups riêng cho EC2 cho phép toàn bộ lưu lượng outbound. Public EC2 đóng vai trò máy trung gian để SSH vào Private EC2. Private EC2 truy cập Internet qua NAT Gateway.

Các CIDR và Availability Zone được cấu hình trong lời gọi module `network` tại `terraform/main.tf`. Nếu thay đổi, cần bảo đảm CIDR subnet nằm trong VPC, không chồng lấn và Availability Zone thuộc region đang sử dụng.

## 2. Điều kiện chuẩn bị

- Cài Git, Terraform CLI, AWS CLI v2, OpenSSH client và curl trong WSL.
- Có tài khoản AWS và credentials có quyền quản lý VPC, subnet, Internet Gateway, NAT Gateway, Elastic IP, Route Tables, Security Groups, EC2 và EC2 key pair.
- Có kết nối Internet để tải Terraform provider và truy cập AWS API.

Kiểm tra các công cụ:

```bash
git --version
terraform version
aws --version
ssh -V
curl --version
```

## 3. Tải mã nguồn

Clone repository này bằng URL trên nút **Code** của GitHub, sau đó mở terminal tại thư mục gốc repository. Các bước tiếp theo giả định thư mục hiện tại chứa thư mục `terraform/`.

Các module Terraform:

| Module | Trách nhiệm |
| --- | --- |
| `terraform/modules/network` | VPC, subnets và Internet Gateway |
| `terraform/modules/routing` | Route Tables, subnet associations, Elastic IP và NAT Gateway |
| `terraform/modules/security` | Default Security Group và hai Security Groups cho EC2 |
| `terraform/modules/compute` | SSH key pair và hai EC2 instance |

## 4. Cấu hình xác thực AWS

Sử dụng credentials hoặc AWS CLI profile được cấp quyền trên tài khoản AWS triển khai.

Lưu bộ credentials được cấp vào `~/.aws/credentials`:

```ini
[default]
aws_access_key_id=YOUR_ACCESS_KEY_ID
aws_secret_access_key=YOUR_SECRET_ACCESS_KEY
aws_session_token=YOUR_SESSION_TOKEN
```

Trường `aws_session_token` chỉ dùng với credentials tạm thời, nếu không phải thì không đưa vào file.

Kiểm tra tài khoản trước khi triển khai:

```bash
aws sts get-caller-identity
```

Kết quả phải trả về đúng tài khoản và danh tính dự định sử dụng. Terraform đọc phương thức xác thực từ AWS profile đang chọn; region của provider được cấu hình trong `terraform/providers.tf`.

## 5. Tạo SSH key và cấu hình IP được phép truy cập

Tạo SSH key nếu chưa có:

```bash
mkdir -p ~/.ssh
ssh-keygen -t ed25519 -f ~/.ssh/nt548-lab01 -C nt548-lab01
```

Không ghi đè key đang được sử dụng. Terraform đọc public key tại `~/.ssh/nt548-lab01.pub` và đăng ký key pair trên AWS. Private key `~/.ssh/nt548-lab01` được giữ trên máy người dùng để SSH.

Lấy địa chỉ IPv4 Internet hiện tại:

```bash
curl -4 https://checkip.amazonaws.com
```

Tạo file `terraform/terraform.tfvars` với nội dung:

```hcl
ssh_cidr = "YOUR_PUBLIC_IPV4/32"
```

Thay `YOUR_PUBLIC_IPV4` bằng IP vừa lấy. Ví dụ, với IP `203.0.113.10`, giá trị là `203.0.113.10/32`.

Nếu đổi mạng hoặc VPN làm thay đổi IP Internet, cập nhật `ssh_cidr` và chạy lại `terraform apply`.

## 6. Triển khai

Từ thư mục gốc repository:

```bash
cd terraform
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

Kiểm tra nội dung plan trước khi nhập `yes` để xác nhận triển khai. Chờ Terraform hiển thị `Apply complete!`.

Xem các outputs:

```bash
terraform output
```

Các outputs được sử dụng trong hướng dẫn:

- `vpc_id`: ID của VPC.
- `public_ec2_ip`: Public IPv4 của Public EC2.
- `private_ec2_ip`: Private IPv4 của Private EC2.

Giữ file `.terraform.lock.hcl` trong Git để lưu phiên bản provider đã chọn. Không commit Terraform state, private key hoặc credentials.

## 7. Kiểm tra kết quả

### 7.1. Kiểm tra trên AWS Console

Đăng nhập [AWS Management Console](https://console.aws.amazon.com/) bằng tài khoản hoặc cổng SSO tương ứng. Chọn region `us-east-1` và bảo đảm đang xem cùng tài khoản với AWS CLI.

- **VPC:** kiểm tra VPC, hai subnet, Internet Gateway và Route Tables. Lọc theo VPC ID để phân biệt với tài nguyên có sẵn.
- **NAT gateways:** NAT Gateway ở trạng thái `Available`, nằm trong Public Subnet và có Elastic IP.
- **Route tables:** Public Route Table có route Internet đến IGW; Private Route Table có route Internet đến NAT Gateway; cả hai được gắn đúng subnet.
- **EC2 → Instances:** hai instance ở trạng thái `Running`, status checks thành công. Chỉ Public EC2 có Public IPv4.
- **Security groups:** Public SG cho SSH từ IP người dùng `/32`; Private SG cho SSH từ Public SG. Tab **Security** của từng EC2 hiển thị SG tương ứng.

### 7.2. SSH vào Public EC2

Trong WSL, tại thư mục `terraform/`:

```bash
PUBLIC_IP=$(terraform output -raw public_ec2_ip)
PRIVATE_IP=$(terraform output -raw private_ec2_ip)

ssh -i ~/.ssh/nt548-lab01 ec2-user@"$PUBLIC_IP"
```

Xác nhận host key khi kết nối lần đầu. Trong Public EC2, chạy:

```bash
hostname
```

Sau khi kiểm tra, chạy `exit` để quay lại terminal WSL.

### 7.3. SSH vào Private EC2 qua Public EC2

Chạy từ terminal WSL, sử dụng các biến IP đã lấy ở trên:

```bash
ssh -i ~/.ssh/nt548-lab01 \
  -o "ProxyCommand=ssh -i $HOME/.ssh/nt548-lab01 -W %h:%p ec2-user@$PUBLIC_IP" \
  ec2-user@"$PRIVATE_IP"
```

Public EC2 chuyển tiếp kết nối đến Private EC2. Không cần sao chép private key lên Public EC2.

Trong Private EC2, chạy:

```bash
hostname
curl -4 --connect-timeout 10 https://checkip.amazonaws.com
```

Kết quả mong đợi:

- Đăng nhập thành công vào Private EC2 thông qua Public EC2.
- Lệnh `curl` trả về địa chỉ IPv4 trùng với Elastic IP của NAT Gateway.

Chạy `exit` sau khi kiểm tra xong.

## 8. Xóa tài nguyên

Sau khi hoàn thành kiểm thử và lưu đủ minh chứng, chạy từ thư mục `terraform/` trên máy WSL:

```bash
terraform plan -destroy
terraform destroy
```

Kiểm tra danh sách tài nguyên rồi nhập `yes`. Chờ thông báo `Destroy complete!` và kiểm tra Console để xác nhận EC2 đã kết thúc, NAT Gateway đã xóa và Elastic IP đã được giải phóng.

Đóng terminal hoặc đăng xuất Console không xóa hạ tầng. Không để NAT Gateway và các tài nguyên tính phí tồn tại khi không còn sử dụng.

Giữ Terraform state cho đến khi xóa hạ tầng thành công. Nếu credentials hết hạn trong quá trình xóa, cập nhật credentials rồi chạy lại `terraform destroy`.

## 9. Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| `ExpiredToken` hoặc token hết hạn | Khởi động/kiểm tra phiên lab và cập nhật credentials tạm thời |
| `AccessDenied` / `UnauthorizedOperation` | Kiểm tra danh tính bằng `aws sts get-caller-identity`, region và giới hạn quyền của lab |
| Không thấy tài nguyên trên Console | Kiểm tra tài khoản, region `us-east-1` và bộ lọc VPC |
| SSH Public EC2 bị timeout | Kiểm tra Public IP hiện tại, IP `/32` trong SG, route đến IGW và trạng thái EC2 |
| SSH báo `Permission denied (publickey)` | Dùng user `ec2-user` và private key khớp với key pair lúc tạo instance |
| SSH Private EC2 bị timeout | Kiểm tra kết nối Public EC2, SG nguồn của Private EC2 và các subnet thuộc cùng VPC |
| Private EC2 không truy cập Internet | Kiểm tra NAT ở trạng thái `Available`, route Private đến NAT và route Public đến IGW |

