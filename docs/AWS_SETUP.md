# AWS Setup Guide

Do this **after** your repo is on GitHub and the `test` job is passing. Use a region close to you (e.g. `ap-south-1` Mumbai). Everything below fits in the AWS free tier / small cost. **Remember to stop/terminate resources after your demo.**

## 1. Create the ECR repository
1. AWS Console → **ECR → Create repository**.
2. Visibility: **Private**, name: `url-shortener`.

## 2. Create an IAM user for GitHub Actions
1. **IAM → Users → Create user** (e.g. `github-actions`).
2. Attach policy **AmazonEC2ContainerRegistryPowerUser**.
3. **Security credentials → Create access key** (use case: "Application running outside AWS"). Save the key ID and secret.

## 3. Create an IAM role for the EC2 instance (to pull images)
1. **IAM → Roles → Create role** → trusted entity **EC2**.
2. Attach **AmazonEC2ContainerRegistryReadOnly**.
3. Name it `ec2-ecr-pull`.

## 4. Launch the EC2 instance
1. **EC2 → Launch instance**.
2. AMI: **Amazon Linux 2023**, type: **t3.micro** (or t2.micro, free-tier eligible).
3. Key pair: create one, download the `.pem` file.
4. Network / Security group, allow inbound:
   - **SSH (22)** from your IP (GitHub Actions runners use changing IPs, so for a student demo you may allow `0.0.0.0/0` on 22. Not recommended for real systems.)
   - **HTTP (80)** from `0.0.0.0/0`
5. **Advanced details → IAM instance profile** → `ec2-ecr-pull`.
6. Launch.

## 5. Install Docker on the instance
SSH in:
```bash
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>
```
Then:
```bash
sudo dnf update -y
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
exit    # log out and back in so the group change applies
```
Amazon Linux 2023 already includes the AWS CLI. Verify with `aws --version` and `docker ps`.

## 6. Add GitHub secrets and variable
Repo → **Settings → Secrets and variables → Actions**.

**Secrets** (tab "Secrets"): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ECR_REPOSITORY` (= `url-shortener`), `EC2_HOST` (public IP), `EC2_USER` (= `ec2-user`), `EC2_SSH_KEY` (paste the entire `.pem` file contents, including the BEGIN/END lines).

**Variable** (tab "Variables"): `DEPLOY_ENABLED` = `true`.

## 7. Deploy
Push any commit to `main` (or **Actions → CI/CD → Re-run all jobs**). When the `deploy` job turns green:
```bash
curl http://<EC2_PUBLIC_IP>/health
curl http://<EC2_PUBLIC_IP>/
```

## Troubleshooting
| Problem | Fix |
|---|---|
| `deploy` job skipped | Variable `DEPLOY_ENABLED` is not `true`, or the push wasn't to `main` |
| ECR login denied in the pipeline | Check IAM user policy and the `AWS_REGION` secret |
| SSH step times out | Security group doesn't allow port 22, or wrong `EC2_HOST` |
| `docker: permission denied` on EC2 | Re-login after `usermod -aG docker ec2-user` |
| `pull access denied` on EC2 | EC2 instance has no IAM role with ECR read access |
| Site unreachable | Security group missing inbound port 80 |

## Cleanup (avoid charges)
Terminate the EC2 instance, delete the ECR repository, and delete the IAM access key.
