# EC2 (Ubuntu) deployment

1. Follow the **Amazon EC2 (Ubuntu) checklist** in [DEPLOYMENT_GUIDE.md](../../DEPLOYMENT_GUIDE.md).
2. Install the systemd unit:

   `sudo cp gt-question-gen.service /etc/systemd/system/`

   Edit paths inside the file if the project is not at `/opt/GT_Question_Gen_2.0`.
3. `sudo systemctl daemon-reload && sudo systemctl enable --now gt-question-gen`

Health check path for your load balancer: **`/api/health`** on port **5000**.
