import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	integrations: [
		starlight({
			title: 'PopKit',
			description: 'AI-powered development workflows for Claude Code',
			social: {
				github: 'https://github.com/jrc1883/popkit',
			},
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Introduction', slug: 'index' },
						{ label: 'Installation', slug: 'getting-started/installation' },
						{ label: 'Quick Start', slug: 'getting-started/quick-start' },
					],
				},
				{
					label: 'Core Concepts',
					items: [
						{ label: 'Agent System', slug: 'concepts/agents' },
						{ label: 'Skills', slug: 'concepts/skills' },
						{ label: 'Commands', slug: 'concepts/commands' },
						{ label: 'Hooks', slug: 'concepts/hooks' },
					],
				},
				{
					label: 'Features',
					items: [
						{ label: 'Power Mode', slug: 'features/power-mode' },
						{ label: 'Feature Development', slug: 'features/feature-dev' },
						{ label: 'Git Workflows', slug: 'features/git-workflows' },
						{ label: 'Morning/Nightly Routines', slug: 'features/routines' },
					],
				},
				{
					label: 'Guides',
					items: [
						{ label: 'Creating Custom Skills', slug: 'guides/custom-skills' },
						{ label: 'Agent Configuration', slug: 'guides/agent-config' },
						{ label: 'Hook Development', slug: 'guides/hooks' },
					],
				},
				{
					label: 'Reference',
					autogenerate: { directory: 'reference' },
				},
			],
			customCss: [
				'./src/styles/custom.css',
			],
		}),
	],
});
