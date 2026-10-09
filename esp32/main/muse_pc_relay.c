/* SPDX-FileCopyrightText: 2026 Muse Waveshare contributors
 * SPDX-License-Identifier: Apache-2.0
 */
#include <netdb.h>
#include <string.h>
#include "sdkconfig.h"
#include "esp_log.h"
int __real_lwip_getaddrinfo(const char *, const char *, const struct addrinfo *, struct addrinfo **);
static int is_muse_service(const char *name) {
    if (!name) return 0;
    const char *suffixes[] = {"muse.ai", "metaaivm.com"};
    size_t n = strlen(name);
    for (unsigned i=0; i<2; i++) {
        size_t m=strlen(suffixes[i]);
        if (n>=m && !strcmp(name+n-m,suffixes[i]) && (n==m || name[n-m-1]=='.')) return 1;
    }
    return 0;
}
int __wrap_lwip_getaddrinfo(const char *name, const char *service,
                       const struct addrinfo *hints, struct addrinfo **result) {
    if (CONFIG_MUSE_PC_RELAY_IP[0] && is_muse_service(name)) {
        ESP_LOGI("muse_relay", "Routing %s through computer %s", name, CONFIG_MUSE_PC_RELAY_IP);
        return __real_lwip_getaddrinfo(CONFIG_MUSE_PC_RELAY_IP, service, hints, result);
    }
    return __real_lwip_getaddrinfo(name, service, hints, result);
}
