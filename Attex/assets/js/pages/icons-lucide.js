/*
Template Name: Attex - Responsive Tailwind Admin Dashboard
Author: CoderThemes
Website: https://coderthemes.com/
Contact: support@coderthemes.com
File: Lucide Icons js
*/

function getIconItem(icon) {
    var div = document.createElement('div'),
        i = document.createElement('i');
    var span = document.createElement('span');
    i.setAttribute("icon-name", icon);
    div.appendChild(i);
    span.innerHTML = icon;
    div.appendChild(span);
    return div;
}
(function () {
    var icons = [
        'accessibility',
        'activity',
        'air-vent',
        'airplay',
        'alarm-check',
        'alarm-clock-off',
        'alarm-clock',
        'alarm-minus',
        'alarm-plus',
        'album',
        'alert-circle',
        'alert-octagon',
        'alert-triangle',
        'align-center-horizontal',
        'align-center-vertical',
        'align-center',
        'align-end-horizontal',
        'align-end-vertical',
        'align-horizontal-distribute-center',
        'align-horizontal-distribute-end',
        'align-horizontal-distribute-start',
        'align-horizontal-justify-center',
        'align-horizontal-justify-end',
        'align-horizontal-justify-start',
        'align-horizontal-space-around',
        'align-horizontal-space-between',
        'align-justify',
        'align-left',
        'align-right',
        'align-start-horizontal',
        'align-start-vertical',
        'align-vertical-distribute-center',
        'align-vertical-distribute-end',
        'align-vertical-distribute-start',
        'align-vertical-justify-center',
        'align-vertical-justify-end',
        'align-vertical-justify-start',
        'align-vertical-space-around',
        'align-vertical-space-between',
        'ampersand',
        'ampersands',
        'anchor',
        'angry',
        'annoyed',
        'aperture',
        'app-window',
        'apple',
        'archive-restore',
        'archive',
        'armchair',
        'arrow-big-down-dash',
        'arrow-big-down',
        'arrow-big-left-dash',
        'arrow-big-left',
        'arrow-big-right-dash',
        'arrow-big-right',
        'arrow-big-up-dash',
        'arrow-big-up',
        'arrow-down-0-1',
        'arrow-down-1-0',
        'arrow-down-a-z',
        'arrow-down-circle',
        'arrow-down-from-line',
        'arrow-down-left-from-circle',
        'arrow-down-left',
        'arrow-down-narrow-wide',
        'arrow-down-right-from-circle',
        'arrow-down-right',
        'arrow-down-square',
        'arrow-down-to-dot',
        'arrow-down-to-line',
        'arrow-down-up',
        'arrow-down-wide-narrow',
        'arrow-down-z-a',
        'arrow-down',
        'arrow-left-circle',
        'arrow-left-from-line',
        'arrow-left-right',
        'arrow-left-square',
        'arrow-left-to-line',
        'arrow-left',
        'arrow-right-circle',
        'arrow-right-from-line',
        'arrow-right-left',
        'arrow-right-square',
        'arrow-right-to-line',
        'arrow-right',
        'arrow-up-0-1',
        'arrow-up-1-0',
        'arrow-up-a-z',
        'arrow-up-circle',
        'arrow-up-down',
        'arrow-up-from-dot',
        'arrow-up-from-line',
        'arrow-up-left-from-circle',
        'arrow-up-left',
        'arrow-up-narrow-wide',
        'arrow-up-right-from-circle',
        'arrow-up-right',
        'arrow-up-square',
        'arrow-up-to-line',
        'arrow-up-wide-narrow',
        'arrow-up-z-a',
        'arrow-up',
        'asterisk',
        'at-sign',
        'atom',
        'award',
        'axe',
        'axis-3d',
        'baby',
        'backpack',
        'badge-alert',
        'badge-check',
        'badge-dollar-sign',
        'badge-help',
        'badge-info',
        'badge-minus',
        'badge-percent',
        'badge-plus',
        'badge-x',
        'badge',
        'baggage-claim',
        'ban',
        'banana',
        'banknote',
        'bar-chart-2',
        'bar-chart-3',
        'bar-chart-4',
        'bar-chart-big',
        'bar-chart-horizontal-big',
        'bar-chart-horizontal',
        'bar-chart',
        'baseline',
        'bath',
        'battery-charging',
        'battery-full',
        'battery-low',
        'battery-medium',
        'battery-warning',
        'battery',
        'beaker',
        'bean-off',
        'bean',
        'bed-double',
        'bed-single',
        'bed',
        'beef',
        'beer',
        'bell-dot',
        'bell-minus',
        'bell-off',
        'bell-plus',
        'bell-ring',
        'bell',
        'bike',
        'binary',
        'biohazard',
        'bird',
        'bitcoin',
        'blinds',
        'bluetooth-connected',
        'bluetooth-off',
        'bluetooth-searching',
        'bluetooth',
        'bold',
        'bomb',
        'bone',
        'book-copy',
        'book-down',
        'book-key',
        'book-lock',
        'book-marked',
        'book-minus',
        'book-open-check',
        'book-open',
        'book-plus',
        'book-template',
        'book-up-2',
        'book-up',
        'book-x',
        'book',
        'bookmark-minus',
        'bookmark-plus',
        'bookmark',
        'bot',
        'box-select',
        'box',
        'boxes',
        'braces',
        'brackets',
        'brain-circuit',
        'brain-cog',
        'brain',
        'briefcase',
        'brush',
        'bug',
        'building-2',
        'building',
        'bus',
        'cake',
        'calculator',
        'calendar-check-2',
        'calendar-check',
        'calendar-clock',
        'calendar-days',
        'calendar-heart',
        'calendar-minus',
        'calendar-off',
        'calendar-plus',
        'calendar-range',
        'calendar-search',
        'calendar-x-2',
        'calendar-x',
        'calendar',
        'camera-off',
        'camera',
        'candlestick-chart',
        'candy-off',
        'candy',
        'car',
        'carrot',
        'case-lower',
        'case-sensitive',
        'case-upper',
        'cast',
        'castle',
        'cat',
        'check-check',
        'check-circle-2',
        'check-circle',
        'check-square',
        'check',
        'chef-hat',
        'cherry',
        'chevron-down-square',
        'chevron-down',
        'chevron-first',
        'chevron-last',
        'chevron-left-square',
        'chevron-left',
        'chevron-right-square',
        'chevron-right',
        'chevron-up-square',
        'chevron-up',
        'chevrons-down-up',
        'chevrons-down',
        'chevrons-left-right',
        'chevrons-left',
        'chevrons-right-left',
        'chevrons-right',
        'chevrons-up-down',
        'chevrons-up',
        'chrome',
        'church',
        'cigarette-off',
        'cigarette',
        'circle-dollar-sign',
        'circle-dot',
        'circle-ellipsis',
        'circle-equal',
        'circle-off',
        'circle-slash-2',
        'circle-slash',
        'circle',
        'circuit-board',
        'citrus',
        'clapperboard',
        'clipboard-check',
        'clipboard-copy',
        'clipboard-edit',
        'clipboard-list',
        'clipboard-paste',
        'clipboard-signature',
        'clipboard-type',
        'clipboard-x',
        'clipboard',
        'clock-1',
        'clock-10',
        'clock-11',
        'clock-12',
        'clock-2',
        'clock-3',
        'clock-4',
        'clock-5',
        'clock-6',
        'clock-7',
        'clock-8',
        'clock-9',
        'clock',
        'cloud-cog',
        'cloud-drizzle',
        'cloud-fog',
        'cloud-hail',
        'cloud-lightning',
        'cloud-moon-rain',
        'cloud-moon',
        'cloud-off',
        'cloud-rain-wind',
        'cloud-rain',
        'cloud-snow',
        'cloud-sun-rain',
        'cloud-sun',
        'cloud',
        'cloudy',
        'clover',
        'club',
        'code-2',
        'code',
        'codepen',
        'codesandbox',
        'coffee',
        'cog',
        'coins',
        'columns',
        'combine',
        'command',
        'compass',
        'component',
        'concierge-bell',
        'construction',
        'contact-2',
        'contact',
        'contrast',
        'cookie',
        'copy-check',
        'copy-minus',
        'copy-plus',
        'copy-slash',
        'copy-x',
        'copy',
        'copyleft',
        'copyright',
        'corner-down-left',
        'corner-down-right',
        'corner-left-down',
        'corner-left-up',
        'corner-right-down',
        'corner-right-up',
        'corner-up-left',
        'corner-up-right',
        'cpu',
        'creative-commons',
        'credit-card',
        'croissant',
        'crop',
        'cross',
        'crosshair',
        'crown',
        'cup-soda',
        'currency',
        'database-backup',
        'database',
        'delete',
        'diamond',
        'dice-1',
        'dice-2',
        'dice-3',
        'dice-4',
        'dice-5',
        'dice-6',
        'dices',
        'diff',
        'disc-2',
        'disc-3',
        'disc',
        'divide-circle',
        'divide-square',
        'divide',
        'dna-off',
        'dna',
        'dog',
        'dollar-sign',
        'door-closed',
        'door-open',
        'dot',
        'download-cloud',
        'download',
        'dribbble',
        'droplet',
        'droplets',
        'drumstick',
        'dumbbell',
        'ear-off',
        'ear',
        'edit-2',
        'edit-3',
        'edit',
        'egg-fried',
        'egg-off',
        'egg',
        'equal-not',
        'equal',
        'eraser',
        'euro',
        'expand',
        'external-link',
        'eye-off',
        'eye',
        'facebook',
        'factory',
        'fan',
        'fast-forward',
        'feather',
        'ferris-wheel',
        'figma',
        'file-archive',
        'file-audio-2',
        'file-audio',
        'file-axis-3d',
        'file-badge-2',
        'file-badge',
        'file-bar-chart-2',
        'file-bar-chart',
        'file-box',
        'file-check-2',
        'file-check',
        'file-clock',
        'file-code-2',
        'file-code',
        'file-cog-2',
        'file-cog',
        'file-diff',
        'file-digit',
        'file-down',
        'file-edit',
        'file-heart',
        'file-image',
        'file-input',
        'file-json-2',
        'file-json',
        'file-key-2',
        'file-key',
        'file-line-chart',
        'file-lock-2',
        'file-lock',
        'file-minus-2',
        'file-minus',
        'file-output',
        'file-pie-chart',
        'file-plus-2',
        'file-plus',
        'file-question',
        'file-scan',
        'file-search-2',
        'file-search',
        'file-signature',
        'file-spreadsheet',
        'file-stack',
        'file-symlink',
        'file-terminal',
        'file-text',
        'file-type-2',
        'file-type',
        'file-up',
        'file-video-2',
        'file-video',
        'file-volume-2',
        'file-volume',
        'file-warning',
        'file-x-2',
        'file-x',
        'file',
        'files',
        'film',
        'filter-x',
        'filter',
        'fingerprint',
        'fish-off',
        'fish',
        'flag-off',
        'flag-triangle-left',
        'flag-triangle-right',
        'flag',
        'flame',
        'flashlight-off',
        'flashlight',
        'flask-conical-off',
        'flask-conical',
        'flask-round',
        'flip-horizontal-2',
        'flip-horizontal',
        'flip-vertical-2',
        'flip-vertical',
        'flower-2',
        'flower',
        'focus',
        'fold-horizontal',
        'fold-vertical',
        'folder-archive',
        'folder-check',
        'folder-clock',
        'folder-closed',
        'folder-cog-2',
        'folder-cog',
        'folder-down',
        'folder-edit',
        'folder-git-2',
        'folder-git',
        'folder-heart',
    ];

    icons.forEach(function (icon) {
        var item = getIconItem(icon);
        document.getElementById('icons').appendChild(item);
    });
})();
