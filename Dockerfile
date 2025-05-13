FROM odoo:18

USER root
RUN mkdir -p /mnt/custom-addons && chown -R odoo:odoo /mnt/custom-addons
USER odoo

COPY --chown=odoo:odoo ./custom_addons /mnt/custom-addons

EXPOSE 8069
EXPOSE 8072