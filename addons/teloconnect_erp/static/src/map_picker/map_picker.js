/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onMounted, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class MapPickerField extends Component {
    static template = "teloconnect_erp.MapPickerField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.mapContainer = useRef("mapContainer");
        this.state = useState({
            googleInput: "",
            detectedAddress: "",
            isGeocoding: false,
        });

        this.map = null;
        this.marker = null;

        onMounted(async () => {
            await this.initMap();
        });

        // Watch for coordinate changes from the record (e.g. if user types manually in lat/lng fields)
        useEffect(
            (lat, lng) => {
                if (this.map && this.marker) {
                    if (this.isValidCoord(lat, lng)) {
                        const cur = this.marker.getLatLng();
                        if (Math.abs(cur.lat - lat) > 0.000001 || Math.abs(cur.lng - lng) > 0.000001) {
                            this.marker.setLatLng([lat, lng]);
                            this.map.panTo([lat, lng]);
                        }
                    }
                }
            },
            () => [this.currentLat, this.currentLng]
        );

        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
        });
    }

    get currentLat() {
        return this.props.record.data.latitude || 0.0;
    }

    get currentLng() {
        return this.props.record.data.longitude || 0.0;
    }

    get currentAddress() {
        return this.props.record.data.installation_address || "";
    }

    get hasValidCoords() {
        return this.isValidCoord(this.currentLat, this.currentLng);
    }

    get googleMapsUrl() {
        return `https://www.google.com/maps?q=${this.currentLat},${this.currentLng}`;
    }

    isValidCoord(lat, lng) {
        return typeof lat === "number" && typeof lng === "number" &&
               lat !== 0.0 && lng !== 0.0 &&
               lat >= -90 && lat <= 90 &&
               lng >= -180 && lng <= 180;
    }

    async initMap() {
        if (!this.mapContainer.el) return;

        // Ensure Leaflet is loaded
        if (typeof window.L === "undefined") {
            let attempts = 0;
            while (typeof window.L === "undefined" && attempts < 25) {
                await new Promise((r) => setTimeout(r, 100));
                attempts++;
            }
        }

        if (typeof window.L === "undefined") {
            console.error("Leaflet no está disponible.");
            return;
        }

        const L = window.L;
        L.Icon.Default.imagePath = "/teloconnect_erp/static/lib/leaflet/images/";

        // Default to Chiclayo center if record has no coordinates yet
        const defaultLat = this.hasValidCoords ? this.currentLat : -6.7714;
        const defaultLng = this.hasValidCoords ? this.currentLng : -79.8409;
        const initialZoom = this.hasValidCoords ? 16 : 13;

        this.map = L.map(this.mapContainer.el, {
            center: [defaultLat, defaultLng],
            zoom: initialZoom,
            zoomControl: true,
        });

        // OpenStreetMap tile layer
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(this.map);

        // Custom red pin with white border and shadow
        const pinIcon = L.divIcon({
            className: "teloconnect-pin",
            html: `
                <div style="
                    width: 32px;
                    height: 32px;
                    background: #dc3545;
                    border: 3px solid #ffffff;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    box-shadow: 0 4px 10px rgba(0,0,0,0.35);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: grab;
                ">
                    <div style="width: 10px; height: 10px; background: #ffffff; border-radius: 50%;"></div>
                </div>
            `,
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32],
        });

        const isDraggable = !this.props.readonly;
        this.marker = L.marker([defaultLat, defaultLng], {
            icon: pinIcon,
            draggable: isDraggable,
        }).addTo(this.map);

        if (isDraggable) {
            // Dragend event on marker
            this.marker.on("dragend", async (ev) => {
                const pos = ev.target.getLatLng();
                await this.applyNewCoords(pos.lat, pos.lng);
            });

            // Click anywhere on map to move marker
            this.map.on("click", async (ev) => {
                const { lat, lng } = ev.latlng;
                this.marker.setLatLng([lat, lng]);
                await this.applyNewCoords(lat, lng);
            });
        }

        // Invalidate map size after mounting
        setTimeout(() => {
            if (this.map) {
                this.map.invalidateSize();
            }
        }, 250);
    }

    async applyNewCoords(lat, lng) {
        const roundedLat = parseFloat(lat.toFixed(7));
        const roundedLng = parseFloat(lng.toFixed(7));
        
        let updates = {
            latitude: roundedLat,
            longitude: roundedLng,
        };

        this.state.isGeocoding = true;
        try {
            // Reverse Geocoding via Nominatim
            const geo = await this.orm.call(
                "teloconnect.backoffice",
                "reverse_geocode_api",
                [roundedLat, roundedLng]
            );

            if (geo && geo.success) {
                if (geo.address) {
                    this.state.detectedAddress = geo.address;
                    updates.installation_address = geo.address;
                }
                if (geo.province) {
                    updates.province = geo.province;
                    if (geo.province === "chiclayo" && geo.district) {
                        updates.district_chiclayo = geo.district;
                        updates.district = geo.district;
                    } else if (geo.province === "lambayeque" && geo.district) {
                        updates.district_lambayeque = geo.district;
                        updates.district = geo.district;
                    } else if (geo.province === "ferrenafe" && geo.district) {
                        updates.district_ferrenafe = geo.district;
                        updates.district = geo.district;
                    }
                }
                const zoneInfo = geo.district ? ` (${geo.district}, ${geo.province})` : "";
                this.notification.add(
                    _t("Dirección y zona actualizadas: ") + (geo.address || "") + zoneInfo,
                    { type: "info" }
                );
            }
        } catch (err) {
            console.warn("Error en reverse geocoding:", err);
        } finally {
            this.state.isGeocoding = false;
        }

        await this.props.record.update(updates);
    }

    async refetchAddress() {
        if (!this.hasValidCoords) return;
        await this.applyNewCoords(this.currentLat, this.currentLng);
    }

    centerOnZone(lat, lng, name) {
        if (!this.map) return;
        this.map.setView([lat, lng], 15);
        if (!this.props.readonly) {
            this.marker.setLatLng([lat, lng]);
            this.applyNewCoords(lat, lng);
            this.notification.add(_t("Ubicación centrada en ") + name, { type: "info" });
        }
    }

    onInputKeyDown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.onApplyCoords();
        }
    }

    async onApplyCoords() {
        const raw = (this.state.googleInput || "").trim();
        if (!raw) return;

        this.state.isGeocoding = true;
        try {
            const res = await this.orm.call(
                "teloconnect.backoffice",
                "resolve_map_input",
                [raw]
            );

            if (res && res.success && (res.latitude || res.address)) {
                let updates = {};
                if (this.isValidCoord(res.latitude, res.longitude)) {
                    const roundedLat = parseFloat(res.latitude.toFixed(7));
                    const roundedLng = parseFloat(res.longitude.toFixed(7));
                    updates.latitude = roundedLat;
                    updates.longitude = roundedLng;

                    if (this.map && this.marker) {
                        this.marker.setLatLng([roundedLat, roundedLng]);
                        this.map.setView([roundedLat, roundedLng], 17);
                    }
                }

                if (res.address) {
                    this.state.detectedAddress = res.address;
                    updates.installation_address = res.address;
                }

                if (res.province) {
                    updates.province = res.province;
                    if (res.province === "chiclayo" && res.district) {
                        updates.district_chiclayo = res.district;
                        updates.district = res.district;
                    } else if (res.province === "lambayeque" && res.district) {
                        updates.district_lambayeque = res.district;
                        updates.district = res.district;
                    } else if (res.province === "ferrenafe" && res.district) {
                        updates.district_ferrenafe = res.district;
                        updates.district = res.district;
                    }
                }

                await this.props.record.update(updates);
                this.state.googleInput = "";
                const msg = res.address
                    ? _t("Ubicación y dirección cargadas: ") + res.address
                    : _t("Coordenadas actualizadas con éxito.");
                this.notification.add(msg, { type: "success" });
            } else {
                this.notification.add(
                    _t("No se pudo identificar la ubicación. Ingrese un enlace de Google Maps, dirección (ej: Libertad 123) o coordenadas."),
                    { type: "warning" }
                );
            }
        } catch (err) {
            console.error("Error al procesar ubicación:", err);
            this.notification.add(_t("Error al comunicarse con el servicio de mapas."), { type: "danger" });
        } finally {
            this.state.isGeocoding = false;
        }
    }
}

export const mapPickerField = {
    component: MapPickerField,
    supportedTypes: ["char"],
};

registry.category("fields").add("map_picker", mapPickerField);
