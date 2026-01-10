FROM node:20-slim

# Install Python 3.11 and typical build dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    gnupg \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    default-jdk \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome (for both Puppeteer and Selenium)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python Setup (Socializer API) ---
COPY requirements.txt ./requirements.txt
COPY socializer-api ./socializer-api

# Create venv and install dependencies
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install -r ./requirements.txt && \
    pip install -e ./socializer-api

# Copy rest of Python Code
COPY radar ./radar
COPY socializer ./socializer

# Setup Start Script - We use CMD directly for API
ENV NODE_ENV=development
ENV PORT=8001

CMD ["/app/venv/bin/uvicorn", "socializer_api.app:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
