# Base images and third-party tools are pinned by digest/commit/sha256 so a
# compromised or re-tagged upstream release can't silently change the image.
FROM golang:1.22@sha256:1cf6c45ba39db9fd6db16922041d074a63c935556a05c5ccb62d181034df7f02 as go-wayback-builder
ARG GO_WAYBACK_COMMIT=bbac309694216e46137d9c7f4363e3d9c9ef546e
RUN git clone https://github.com/Abhinandan-Khurana/go-wayback.git && git -C go-wayback checkout --detach ${GO_WAYBACK_COMMIT}
WORKDIR go-wayback
RUN GOOS=linux GOARCH=amd64 go build -o go-wayback v2/main.go
RUN chmod +x go-wayback
RUN cp go-wayback /usr/bin/

FROM --platform=linux/amd64 python:3.9-slim@sha256:2d97f6910b16bd338d3060f261f53f144965f755599aab1acda1e13cf1731b1b

# Install wget
RUN apt-get update && apt-get install -y wget unzip tar gcc libpcap-dev dnsutils git dnstwist

# Install git
RUN apt-get update --fix-missing && apt install git -y

# Setup work directory
WORKDIR /home/mantis

# Install subfinder 
RUN echo "Installing subfinder"
RUN wget https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip
RUN echo "6fda32fe1f5750e63fa07c112b1b615d033e425c6dc6659ed8ec61035eb8eba2  subfinder_2.6.6_linux_amd64.zip" | sha256sum -c -
RUN unzip subfinder_2.6.6_linux_amd64.zip
RUN mv subfinder /usr/bin
RUN rm -rf *

# Install Go_Virustotal
RUN echo "Installing Go_Virustotal"
RUN wget https://github.com/Abhinandan-Khurana/go_virustotal/releases/download/v1.0.1/go_virustotal-linux-v1.0.1
RUN echo "b193842634268327a669fed72df868f2cd61ad4694f5c38e73601de2a68c2188  go_virustotal-linux-v1.0.1" | sha256sum -c -
RUN mv go_virustotal-linux-v1.0.1 go_virustotal
RUN chmod +x go_virustotal
RUN mv go_virustotal /usr/bin/

# Install Go_Wayback
COPY --from=go-wayback-builder /usr/bin/go-wayback /usr/bin

# Install HTTPX
RUN echo "Installing HTTPX"
RUN wget https://github.com/projectdiscovery/httpx/releases/download/v1.6.8/httpx_1.6.8_linux_amd64.zip
RUN echo "b91c2a115085353f7bbd5bc52604da1dc386530ad3087b745a50f800afd8d9d1  httpx_1.6.8_linux_amd64.zip" | sha256sum -c -
RUN unzip httpx_1.6.8_linux_amd64.zip
RUN mv httpx /usr/bin
RUN rm -rf *

# Install Findcdn
RUN echo "Installing Findcdn"
RUN pip install git+https://github.com/cisagov/findcdn.git@7bbf50e4a1cf1f32999c1abdcabc064d8ebf53f8

# Install Ipinfo
RUN echo "Installing Ipinfo"
RUN wget https://github.com/ipinfo/cli/releases/download/ipinfo-3.3.1/ipinfo_3.3.1_linux_amd64.tar.gz
RUN echo "81e62958fcb91f979c03d0f10887486df1460d432d0d4c2e86a3079f6039840a  ipinfo_3.3.1_linux_amd64.tar.gz" | sha256sum -c -
RUN tar -xvf ipinfo_3.3.1_linux_amd64.tar.gz
RUN mv ipinfo_3.3.1_linux_amd64 ipinfo
RUN mv ipinfo /usr/bin
RUN rm -rf *

# Install naabu
RUN echo "Installing naabu"
RUN wget https://github.com/projectdiscovery/naabu/releases/download/v2.1.9/naabu_2.1.9_linux_amd64.zip
RUN echo "17acaf7824514a891f6523d62fa1a0df7b47084c463f5778e0232a5555574792  naabu_2.1.9_linux_amd64.zip" | sha256sum -c -
RUN unzip naabu_2.1.9_linux_amd64.zip
RUN mv naabu /usr/bin
RUN rm -rf *

# Install nuclei
RUN echo "Installing nuclei"
RUN wget https://github.com/projectdiscovery/nuclei/releases/download/v3.3.4/nuclei_3.3.4_linux_amd64.zip
RUN echo "b3c880d9516e9e73ea0b77dd53cc7b15035544403857efb01974979f7ae4125a  nuclei_3.3.4_linux_amd64.zip" | sha256sum -c -
RUN unzip nuclei_3.3.4_linux_amd64.zip
RUN mv nuclei /usr/bin
RUN rm -rf *

# Install gitleaks 
RUN echo "Installing gitleaks"
RUN wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.1/gitleaks_8.18.1_linux_x64.tar.gz
RUN echo "3e157a26081e296d4cb94ef0d87441c9afc5f392cb02957656dd5cfeb7aaf6c9  gitleaks_8.18.1_linux_x64.tar.gz" | sha256sum -c -
RUN tar -xvf gitleaks_8.18.1_linux_x64.tar.gz
RUN mv gitleaks /usr/bin
RUN rm -rf *

# Install wafw00f
RUN pip install wafw00f

#Install gau
RUN echo "Installing GAU"
RUN wget https://github.com/lc/gau/releases/download/v2.2.1/gau_2.2.1_linux_amd64.tar.gz
RUN echo "b9e18c51a53161929c3099aada80cb4b7b19b8f72b097bbb4066f24b358bf756  gau_2.2.1_linux_amd64.tar.gz" | sha256sum -c -
RUN tar -xvf gau_2.2.1_linux_amd64.tar.gz
RUN mv gau /usr/bin
RUN rm -rf *

# Installing Corsy
RUN echo "Installing Corsy"
RUN wget https://github.com/s0md3v/Corsy/archive/refs/tags/1.0-rc.zip
RUN echo "290e9cc2c1e35bb6440e58c02924bfb4f4e611c6acf9d714d5ea7b2fa5a97b87  1.0-rc.zip" | sha256sum -c -
RUN unzip 1.0-rc.zip
RUN mv Corsy-1.0-rc Corsy
RUN mv Corsy /usr/bin
RUN rm -rf *

# Install Poetry
RUN pip install poetry==1.4.2

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Setup Poetry ENV variables
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=0 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* /home/mantis/

# Install dependencies using Poetry
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# Creating Mantis alias
RUN echo 'export PS1="🦗 Mantis > " && \
alias mantis="python /home/mantis/launch.py" && \
alias help="python /home/mantis/launch.py --help"' | tee -a ~/.bashrc

RUN echo 'echo -e "\033[1;94mWelcome to Mantis Shell! Enter help for more details\033[0m"' | tee -a ~/.bashrc

# Copy Code
COPY ./mantis /home/mantis/mantis
COPY ./configs /home/mantis/configs
COPY ./launch.py /home/mantis/launch.py
COPY ./scheduler.py /home/mantis/scheduler.py
COPY ./*.txt /home/mantis/

# Create Directories
RUN mkdir /home/mantis/logs
RUN mkdir /home/mantis/logs/scan_efficiency
RUN mkdir /home/mantis/logs/tool_logs

# Required for displaying stdout sequentially
ENV PYTHONUNBUFFERED=1
