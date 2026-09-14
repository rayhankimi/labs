# lab project for devops learning purposes

Assuming EC2 Ubuntu 26.04.

structure:
```
fastapi-lab/
  .github/workflows    # ci/cd pipeline
  app/main.py          # app
  requirements.txt
  deploy/myapp.service # systemd
  deploy/env.example   # EnvironmentFile
  deploy/nginx-myapp.conf
  deploy/logrotate-myapp
```


