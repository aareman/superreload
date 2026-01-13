import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// Read the Docs sets READTHEDOCS=True and serves from /en/latest/
const isReadTheDocs = process.env.READTHEDOCS === 'True';

const config: Config = {
  title: 'superreload',
  tagline: 'True hot reload for Django and Python web frameworks',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: isReadTheDocs ? 'https://superreload.readthedocs.io' : 'https://superreload.dev',
  baseUrl: isReadTheDocs ? '/en/latest/' : '/',

  organizationName: 'superreload',
  projectName: 'superreload',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/aareman/superreload/tree/main/docs/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/superreload-social-card.png',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'superreload',
      logo: {
        alt: 'superreload Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/aareman/superreload',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Getting Started',
              to: '/docs/getting-started',
            },
            {
              label: 'Django Setup',
              to: '/docs/django',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/aareman/superreload',
            },
            {
              label: 'PyPI',
              href: 'https://pypi.org/project/superreload/',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} superreload contributors. MIT License.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
