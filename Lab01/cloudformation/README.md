# NT548 Lab01 - CloudFormation

Triển khai hạ tầng AWS bằng CloudFormation, gồm VPC, Public Subnet, Private Subnet, Internet Gateway, NAT Gateway, Route Tables, hai EC2 instance và Security Groups.

Các lệnh dưới đây dùng cú pháp Bash. Chạy trong cùng terminal Bash; nếu dùng PowerShell, cần đổi cú pháp biến, đường dẫn và nối dòng tương ứng.

## Triển khai từng giai đoạn để chụp báo cáo

Sửa templates tăng dần rồi chạy trực tiếp `aws cloudformation package` và `aws cloudformation deploy` sau mỗi lần sửa. Không dùng script hoặc parameter `Stage`. Hiện `main.yaml` chỉ có `NetworkStack`; routing chưa có NAT. Các module chưa được root tham chiếu sẽ không được triển khai.

| Thứ tự | STAGE | Tài nguyên bổ sung | Ảnh cần chụp trước bước tiếp |
| --- | --- | --- | --- |
| 1 | `network` | VPC, subnets, IGW; AWS tự tạo default SG | CLI deploy, VPC, subnets, IGW, default SG |
| 2 | `routing` | Route tables, associations, public default route | CLI deploy, public routes, private routes chỉ local |
| 3 | `nat` | EIP, NAT Gateway, private default route | CLI deploy, NAT/EIP, private routes |
| 4 | `compute` | Import public key, hai EC2 dùng default SG | CLI deploy, EC2 |
| 5 | `security` | Hai SG riêng, cập nhật SG gắn trên EC2 | CLI deploy, SG rules, SSH Public/Private, IP NAT |

Bảng trên là thứ tự chỉnh sửa, không phải giá trị parameter. Giữ nguyên logical IDs và các resources đã deploy khi thêm bước tiếp theo. Dừng chụp CLI/Console sau mỗi deploy. Bước EC2 chưa cho phép SSH từ Internet; kiểm thử sau bước Security Groups. AWS tự tạo default SG cùng VPC; rules được giữ nguyên.

### Lệnh cho bước 1 hiện tại

Chạy trong terminal Bash, tại thư mục `cloudformation/`:

```bash
aws cloudformation package \
  --template-file main.yaml \
  --s3-bucket nt548-lab01-cfn-398654539858 \
  --s3-prefix nt548-lab01 \
  --output-template-file packaged.yaml \
  --region us-east-1

aws cloudformation deploy \
  --template-file packaged.yaml \
  --stack-name nt548-lab01-cfn \
  --region us-east-1 \
  --no-cli-pager
```

Chụp dòng deploy thành công và Console VPC, subnets, IGW, default SG trước khi thêm RoutingStack. Bước này không nhận parameters SSH. Các mục bên dưới mô tả cấu hình đích sau khi hoàn tất năm bước; lệnh truyền parameters SSH chỉ dùng khi đã bổ sung parameters tương ứng vào root.

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

Hai Security Groups riêng cho EC2 cho phép toàn bộ lưu lượng outbound. Public EC2 đóng vai trò máy trung gian để SSH vào Private EC2. Private EC2 truy cập Internet qua NAT Gateway.

Các CIDR và Availability Zone là parameters của root stack trong `cloudformation/main.yaml`. Nếu thay đổi, cần bảo đảm CIDR subnet nằm trong VPC, không chồng lấn và Availability Zone thuộc region đang sử dụng.

## 2. Điều kiện chuẩn bị

- Cài Git, AWS CLI v2, OpenSSH client và curl trên máy chạy lệnh; bảo đảm các công cụ có trong `PATH` của terminal.
- Có tài khoản AWS và credentials có quyền quản lý CloudFormation, S3, VPC, subnet, Internet Gateway, NAT Gateway, Elastic IP, Route Tables, Security Groups, EC2 và EC2 key pair.
- Có một S3 bucket trong `us-east-1` để lưu nested templates.

Kiểm tra các công cụ:

```bash
git --version
aws --version
ssh -V
curl --version
```

## 3. Cấu trúc CloudFormation

Clone repository, sau đó mở terminal tại thư mục `cloudformation/`.

| Template | Trách nhiệm |
| --- | --- |
| `main.yaml` | Root stack, truyền parameters và outputs giữa nested stacks |
| `templates/network.yaml` | VPC, subnets và Internet Gateway |
| `templates/routing.yaml` | Route Tables, subnet associations, Elastic IP và NAT Gateway |
| `templates/security.yaml` | Hai Security Groups cho EC2 |
| `templates/compute.yaml` | SSH key pair và hai EC2 instance |

CloudFormation không hỗ trợ chỉnh rules của default Security Group hiện hữu bằng resource native. Hai EC2 chỉ gắn Security Groups riêng nên default Security Group không được sử dụng.

## 4. Cấu hình xác thực AWS

Lưu credentials được cấp vào `~/.aws/credentials`:

```ini
[default]
aws_access_key_id=YOUR_ACCESS_KEY_ID
aws_secret_access_key=YOUR_SECRET_ACCESS_KEY
aws_session_token=YOUR_SESSION_TOKEN
```

Trường `aws_session_token` chỉ dùng với credentials tạm thời.

Kiểm tra đúng tài khoản trước khi triển khai:

```bash
aws sts get-caller-identity
```

## 5. Tạo SSH key và lấy IP truy cập

Tạo SSH key nếu chưa có:

```bash
mkdir -p ~/.ssh
ssh-keygen -t ed25519 -f ~/.ssh/nt548-lab01 -C nt548-lab01
```

Không ghi đè key đang được sử dụng. Private key `~/.ssh/nt548-lab01` chỉ được giữ trên máy người dùng.

Lấy địa chỉ IPv4 Internet hiện tại và đọc public key:

```bash
SSH_CIDR="$(curl -4 -s https://checkip.amazonaws.com)/32"
SSH_PUBLIC_KEY="$(cat ~/.ssh/nt548-lab01.pub)"
printf 'SSH CIDR: %s\n' "$SSH_CIDR"
```

Nếu đổi mạng hoặc VPN, triển khai lại stack với `SSH_CIDR` mới.

## 6. Kiểm tra và triển khai

Từ thư mục `cloudformation/`, kiểm tra root template:

```bash
aws cloudformation validate-template \
  --template-body file://main.yaml \
  --region us-east-1
```

Đóng gói nested templates. Thay `YOUR_BUCKET` bằng bucket S3 đã chuẩn bị:

```bash
aws cloudformation package \
  --template-file main.yaml \
  --s3-bucket YOUR_BUCKET \
  --s3-prefix nt548-lab01 \
  --output-template-file packaged.yaml \
  --region us-east-1
```

Lệnh `package` upload các file trong `templates/` và thay đường dẫn local bằng URL S3.

Triển khai stack:

```bash
aws cloudformation deploy \
  --template-file packaged.yaml \
  --stack-name nt548-lab01 \
  --parameter-overrides \
    SshCidr="$SSH_CIDR" \
    SshPublicKey="$SSH_PUBLIC_KEY" \
  --region us-east-1
```

Xem outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name nt548-lab01 \
  --query 'Stacks[0].Outputs' \
  --output table \
  --region us-east-1
```

Các outputs chính:

- `VpcId`: ID của VPC.
- `PublicEc2Ip`: Public IPv4 của Public EC2.
- `PrivateEc2Ip`: Private IPv4 của Private EC2.
- `NatElasticIp`: Elastic IP của NAT Gateway.

Không commit `packaged.yaml`, private key hoặc credentials.

## 7. Kiểm tra kết quả

### 7.1. Kiểm tra trên AWS Console

Chọn region `us-east-1` và đúng tài khoản đã kiểm tra bằng AWS CLI.

- **CloudFormation:** root stack và bốn nested stacks ở trạng thái `CREATE_COMPLETE` hoặc `UPDATE_COMPLETE`.
- **VPC:** VPC, hai subnet, Internet Gateway và Route Tables tồn tại đúng cấu hình.
- **NAT gateways:** NAT Gateway ở trạng thái `Available`, nằm trong Public Subnet và có Elastic IP.
- **Route tables:** Public route đến IGW; Private route đến NAT Gateway; mỗi route table gắn đúng subnet.
- **EC2:** hai instance ở trạng thái `Running`; chỉ Public EC2 có Public IPv4.
- **Security groups:** Public SG nhận SSH từ IP người dùng; Private SG nhận SSH từ Public SG.

### 7.2. SSH vào Public EC2

Lấy IP từ stack outputs:

```bash
PUBLIC_IP=$(aws cloudformation describe-stacks \
  --stack-name nt548-lab01 \
  --query "Stacks[0].Outputs[?OutputKey=='PublicEc2Ip'].OutputValue" \
  --output text \
  --region us-east-1)

PRIVATE_IP=$(aws cloudformation describe-stacks \
  --stack-name nt548-lab01 \
  --query "Stacks[0].Outputs[?OutputKey=='PrivateEc2Ip'].OutputValue" \
  --output text \
  --region us-east-1)

ssh -i ~/.ssh/nt548-lab01 ec2-user@"$PUBLIC_IP"
```

Trong Public EC2, chạy `hostname`, sau đó `exit`.

### 7.3. SSH vào Private EC2 qua Public EC2

```bash
ssh -i ~/.ssh/nt548-lab01 \
  -o "ProxyCommand=ssh -i $HOME/.ssh/nt548-lab01 -W %h:%p ec2-user@$PUBLIC_IP" \
  ec2-user@"$PRIVATE_IP"
```

Trong Private EC2:

```bash
hostname
curl -4 --connect-timeout 10 https://checkip.amazonaws.com
```

Kết quả `curl` phải trùng với output `NatElasticIp`. Chạy `exit` sau khi kiểm tra.

## 8. Xóa tài nguyên

```bash
aws cloudformation delete-stack \
  --stack-name nt548-lab01 \
  --region us-east-1

aws cloudformation wait stack-delete-complete \
  --stack-name nt548-lab01 \
  --region us-east-1
```

Kiểm tra Console để xác nhận root stack, nested stacks, EC2, NAT Gateway và Elastic IP đã bị xóa. Xóa objects trong S3 nếu không còn dùng.

Đóng terminal hoặc đăng xuất Console không xóa hạ tầng. Không để NAT Gateway tồn tại khi không còn sử dụng.

## 9. Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| `ExpiredToken` hoặc token hết hạn | Cập nhật credentials tạm thời rồi chạy lại lệnh |
| `AccessDenied` / `UnauthorizedOperation` | Kiểm tra IAM permissions, tài khoản và region bằng `aws sts get-caller-identity` |
| `Unable to upload artifact` | Kiểm tra bucket tồn tại trong `us-east-1` và có quyền `s3:PutObject` |
| Nested stack rollback | Mở tab **Events** của nested stack lỗi để xem resource gây lỗi đầu tiên |
| Stack kẹt `ROLLBACK_COMPLETE` | Xóa stack rồi triển khai lại sau khi sửa nguyên nhân |
| SSH Public EC2 bị timeout | Kiểm tra IP `/32`, public route, Public IP và trạng thái EC2 |
| SSH báo `Permission denied (publickey)` | Dùng user `ec2-user` và private key khớp public key đã truyền khi deploy |
| SSH Private EC2 bị timeout | Kiểm tra Public EC2, Private SG và hai subnet thuộc cùng VPC |
| Private EC2 không truy cập Internet | Kiểm tra NAT ở trạng thái `Available` và Private route trỏ đến NAT Gateway |
