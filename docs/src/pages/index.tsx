import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          🔥 {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/">
            Get Started
          </Link>
          <Link
            className="button button--outline button--secondary button--lg"
            style={{marginLeft: '1rem'}}
            href="https://github.com/aareman/superreload">
            GitHub
          </Link>
        </div>
      </div>
    </header>
  );
}

function Feature({title, description}: {title: string; description: string}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

function HomepageFeatures() {
  const features = [
    {
      title: 'Instant Reload',
      description: 'Python modules reload without restarting the server. No more waiting for Django to restart.',
    },
    {
      title: 'CSS Hot Reload',
      description: 'Stylesheets update instantly without page refresh. See your changes immediately.',
    },
    {
      title: 'Error Overlay',
      description: 'Beautiful error display with stack traces and local variables. Fix errors without leaving your browser.',
    },
  ];

  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {features.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="Hot Reload for Django"
      description="True hot reload for Django and Python web frameworks. No server restart needed.">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <section style={{padding: '2rem 0', textAlign: 'center'}}>
          <div className="container">
            <Heading as="h2">Quick Start</Heading>
            <pre style={{
              display: 'inline-block',
              textAlign: 'left',
              padding: '1.5rem',
              background: '#1e1e1e',
              color: '#d4d4d4',
              borderRadius: '8px',
              fontSize: '0.9rem',
            }}>
{`pip install superreload[django]

# settings.py
INSTALLED_APPS = ['superreload.frameworks.django', ...]
MIDDLEWARE = ['superreload.frameworks.django.SuperReloadMiddleware', ...]

# Run
python manage.py superreload`}
            </pre>
          </div>
        </section>
      </main>
    </Layout>
  );
}
