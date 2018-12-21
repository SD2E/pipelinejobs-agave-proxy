FROM sd2e/reactors:python3-edge

ARG DATACATALOG_BRANCH=agave_proxy

# Comment out if not actively developing python-datacatalog
RUN pip uninstall --yes datacatalog || true

# Install from Repo until release
RUN pip3 install --upgrade --no-cache-dir \
    git+https://github.com/SD2E/python-datacatalog.git@${DATACATALOG_BRANCH}
