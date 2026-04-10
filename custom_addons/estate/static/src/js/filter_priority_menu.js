odoo.define('estate.filter_priority_menu', function (require) {
    "use strict";

    const FilterMenu = require('web.FilterMenu');

    const PRIORITY_PARENT_ID = '__estate_priority_parent__';

    const itemsDescriptor = Object.getOwnPropertyDescriptor(FilterMenu.prototype, 'items');
    const originalGetItems = itemsDescriptor && itemsDescriptor.get;
    const originalOnItemSelected = FilterMenu.prototype._onItemSelected;

    function getPriorityLevel(item) {
        if (!item || !item.domain || item.type !== 'filter') {
            return null;
        }
        const domain = String(item.domain);
        if (!domain.includes("priority_level")) {
            return null;
        }
        if (domain.includes("'high'")) {
            return 'high';
        }
        if (domain.includes("'normal'")) {
            return 'normal';
        }
        if (domain.includes("'low'")) {
            return 'low';
        }
        return null;
    }

    function extractPriorityMap(items) {
        const priorityMap = {
            high: null,
            normal: null,
            low: null,
        };
        items.forEach((item) => {
            const level = getPriorityLevel(item);
            if (level) {
                priorityMap[level] = item;
            }
        });
        return priorityMap;
    }

    function hasAnyPriority(priorityMap) {
        return Boolean(priorityMap.high || priorityMap.normal || priorityMap.low);
    }

    Object.defineProperty(FilterMenu.prototype, 'items', {
        get() {
            const items = originalGetItems.call(this);
            const priorityMap = extractPriorityMap(items);
            if (!hasAnyPriority(priorityMap)) {
                return items;
            }

            const options = [];
            ['high', 'normal', 'low'].forEach((level) => {
                const item = priorityMap[level];
                if (item) {
                    options.push({
                        id: item.id,
                        description: item.description,
                        isActive: item.isActive,
                        groupNumber: item.groupNumber,
                    });
                }
            });

            const isPriorityItem = (item) => Boolean(getPriorityLevel(item));
            const firstPriorityIndex = items.findIndex(isPriorityItem);
            const nonPriorityBefore = items.slice(0, firstPriorityIndex).filter((item) => !isPriorityItem(item)).length;
            const cleanItems = items.filter((item) => !isPriorityItem(item));

            cleanItems.splice(nonPriorityBefore, 0, {
                id: PRIORITY_PARENT_ID,
                description: 'Ưu tiên',
                isActive: options.some((option) => option.isActive),
                groupNumber: options[0] && options[0].groupNumber,
                options,
            });

            return cleanItems;
        },
    });

    FilterMenu.prototype._onItemSelected = function (ev) {
        const detail = ev.detail || {};
        const item = detail.item;
        const option = detail.option;

        if (item && item.id === PRIORITY_PARENT_ID && option) {
            ev.stopPropagation();
            const allItems = originalGetItems.call(this);
            const priorityItems = allItems.filter((filterItem) => Boolean(getPriorityLevel(filterItem)));

            priorityItems.forEach((priorityItem) => {
                if (priorityItem.id !== option.id && priorityItem.isActive) {
                    this.model.dispatch('toggleFilter', priorityItem.id);
                }
            });

            this.model.dispatch('toggleFilter', option.id);
            return;
        }

        return originalOnItemSelected.call(this, ev);
    };
});
