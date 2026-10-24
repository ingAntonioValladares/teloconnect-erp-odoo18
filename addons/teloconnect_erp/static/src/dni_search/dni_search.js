/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class DniSearchField extends Component {
    static template = "teloconnect_erp.DniSearchField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.inputRef = useRef("inputRef");
        this.state = useState({
            isSearching: false,
            statusMessage: "",
            statusType: "",
        });
    }

    get currentValue() {
        return this.props.record.data[this.props.name] || "";
    }

    onInputChange(ev) {
        const val = ev.target.value.trim();
        this.props.record.update({ [this.props.name]: val });
    }

    onKeyDown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.onSearchClick();
        }
    }

    async onSearchClick() {
        const inputEl = this.inputRef.el;
        const dni = (inputEl ? inputEl.value : this.currentValue).trim();
        if (!dni || dni.length !== 8 || !/^\d+$/.test(dni)) {
            this.state.statusMessage = _t("El DNI debe tener exactamente 8 dígitos numéricos.");
            this.state.statusType = "danger";
            return;
        }

        this.state.isSearching = true;
        this.state.statusMessage = _t("Consultando en padrón / RENIEC...");
        this.state.statusType = "info";

        try {
            const res = await this.orm.call(
                "teloconnect.backoffice",
                "search_dni_api",
                [dni]
            );

            if (res && res.success && res.name) {
                await this.props.record.update({
                    [this.props.name]: dni,
                    client_name: res.name,
                });
                this.state.statusMessage = _t("Cliente: ") + res.name;
                this.state.statusType = "success";
                this.notification.add(_t("Nombre encontrado y completado: ") + res.name, {
                    type: "success",
                });
            } else {
                const errMsg = (res && res.error) || _t("No se encontró información para el DNI.");
                this.state.statusMessage = errMsg;
                this.state.statusType = "warning";
                this.notification.add(errMsg, { type: "warning" });
            }
        } catch (err) {
            console.error("Error al consultar DNI:", err);
            const msg = (err && err.data && err.data.message) || _t("Error de conexión al consultar DNI.");
            this.state.statusMessage = msg;
            this.state.statusType = "danger";
            this.notification.add(msg, { type: "danger" });
        } finally {
            this.state.isSearching = false;
        }
    }
}

export const dniSearchField = {
    component: DniSearchField,
    supportedTypes: ["char"],
};

registry.category("fields").add("dni_search", dniSearchField);
