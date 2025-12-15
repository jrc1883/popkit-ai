/**
 * PopKit Benchmark Framework - Config Switcher
 *
 * Manages PopKit plugin state for A/B/C benchmark comparisons:
 * - Vanilla: PopKit disabled
 * - PopKit: PopKit enabled (free tier)
 * - Power/Pro: PopKit enabled with pro credentials
 */

import { rename, access, mkdir, writeFile, readFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { homedir } from 'node:os';
import type { BenchmarkMode } from '../types.js';

/**
 * Configuration for the config switcher
 */
export interface ConfigSwitcherOptions {
  /** Claude plugins directory (default: ~/.claude/plugins) */
  pluginsDir?: string;
  /** PopKit plugin name in marketplace (default: popkit-marketplace) */
  pluginName?: string;
  /** Pro credentials file path */
  proCredentialsPath?: string;
  /** Whether to log operations */
  verbose?: boolean;
}

/**
 * State snapshot for restoration
 */
export interface ConfigSnapshot {
  mode: BenchmarkMode;
  pluginEnabled: boolean;
  proEnabled: boolean;
  timestamp: string;
}

/**
 * Manages PopKit configuration for benchmark modes
 */
export class ConfigSwitcher {
  private pluginsDir: string;
  private pluginName: string;
  private pluginPath: string;
  private disabledPath: string;
  private proCredentialsPath: string;
  private verbose: boolean;
  private originalSnapshot: ConfigSnapshot | null = null;

  constructor(options: ConfigSwitcherOptions = {}) {
    this.pluginsDir = options.pluginsDir || join(homedir(), '.claude', 'plugins', 'marketplaces');
    this.pluginName = options.pluginName || 'popkit-marketplace';
    this.pluginPath = join(this.pluginsDir, this.pluginName);
    this.disabledPath = join(this.pluginsDir, `${this.pluginName}.disabled`);
    this.proCredentialsPath = options.proCredentialsPath || join(homedir(), '.popkit', 'config', 'pro-credentials.json');
    this.verbose = options.verbose || false;
  }

  /**
   * Log message if verbose mode is enabled
   */
  private log(message: string): void {
    if (this.verbose) {
      console.log(`[ConfigSwitcher] ${message}`);
    }
  }

  /**
   * Check if a path exists
   */
  private async exists(path: string): Promise<boolean> {
    try {
      await access(path);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if PopKit plugin is currently enabled
   */
  async isPluginEnabled(): Promise<boolean> {
    return await this.exists(this.pluginPath);
  }

  /**
   * Check if pro credentials are configured
   */
  async isProEnabled(): Promise<boolean> {
    if (!(await this.exists(this.proCredentialsPath))) {
      return false;
    }
    try {
      const content = await readFile(this.proCredentialsPath, 'utf-8');
      const creds = JSON.parse(content);
      return !!(creds.apiKey || creds.token);
    } catch {
      return false;
    }
  }

  /**
   * Get current configuration state
   */
  async getCurrentState(): Promise<ConfigSnapshot> {
    const pluginEnabled = await this.isPluginEnabled();
    const proEnabled = await this.isProEnabled();

    let mode: BenchmarkMode = 'vanilla';
    if (pluginEnabled) {
      mode = proEnabled ? 'power' : 'popkit';
    }

    return {
      mode,
      pluginEnabled,
      proEnabled,
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Save current state for later restoration
   */
  async saveSnapshot(): Promise<ConfigSnapshot> {
    this.originalSnapshot = await this.getCurrentState();
    this.log(`Saved snapshot: ${JSON.stringify(this.originalSnapshot)}`);
    return this.originalSnapshot;
  }

  /**
   * Disable PopKit plugin (for vanilla mode)
   */
  async disablePlugin(): Promise<void> {
    if (!(await this.isPluginEnabled())) {
      this.log('Plugin already disabled');
      return;
    }

    try {
      await rename(this.pluginPath, this.disabledPath);
      this.log('Plugin disabled (renamed to .disabled)');
    } catch (error) {
      throw new Error(`Failed to disable plugin: ${error}`);
    }
  }

  /**
   * Enable PopKit plugin
   */
  async enablePlugin(): Promise<void> {
    if (await this.isPluginEnabled()) {
      this.log('Plugin already enabled');
      return;
    }

    if (!(await this.exists(this.disabledPath))) {
      throw new Error('Plugin not found (neither enabled nor disabled path exists)');
    }

    try {
      await rename(this.disabledPath, this.pluginPath);
      this.log('Plugin enabled (restored from .disabled)');
    } catch (error) {
      throw new Error(`Failed to enable plugin: ${error}`);
    }
  }

  /**
   * Clear pro credentials (for free tier mode)
   */
  async clearProCredentials(): Promise<void> {
    if (!(await this.isProEnabled())) {
      this.log('Pro credentials already cleared');
      return;
    }

    const backupPath = `${this.proCredentialsPath}.backup`;
    try {
      // Backup existing credentials
      const content = await readFile(this.proCredentialsPath, 'utf-8');
      await writeFile(backupPath, content);

      // Write empty credentials
      await writeFile(this.proCredentialsPath, JSON.stringify({ enabled: false }, null, 2));
      this.log('Pro credentials cleared (backed up)');
    } catch (error) {
      throw new Error(`Failed to clear pro credentials: ${error}`);
    }
  }

  /**
   * Restore pro credentials from backup
   */
  async restoreProCredentials(): Promise<void> {
    const backupPath = `${this.proCredentialsPath}.backup`;
    if (!(await this.exists(backupPath))) {
      this.log('No pro credentials backup found');
      return;
    }

    try {
      const content = await readFile(backupPath, 'utf-8');
      await writeFile(this.proCredentialsPath, content);
      await rm(backupPath);
      this.log('Pro credentials restored from backup');
    } catch (error) {
      throw new Error(`Failed to restore pro credentials: ${error}`);
    }
  }

  /**
   * Switch to a specific benchmark mode
   */
  async switchMode(mode: BenchmarkMode): Promise<void> {
    this.log(`Switching to mode: ${mode}`);

    switch (mode) {
      case 'vanilla':
        // Disable PopKit entirely
        await this.disablePlugin();
        break;

      case 'popkit':
        // Enable PopKit but disable pro
        await this.enablePlugin();
        await this.clearProCredentials();
        break;

      case 'power':
        // Enable PopKit with pro credentials
        await this.enablePlugin();
        await this.restoreProCredentials();
        break;

      default:
        throw new Error(`Unknown mode: ${mode}`);
    }

    this.log(`Mode switched to: ${mode}`);
  }

  /**
   * Restore original configuration
   */
  async restore(): Promise<void> {
    if (!this.originalSnapshot) {
      this.log('No snapshot to restore');
      return;
    }

    this.log(`Restoring to original mode: ${this.originalSnapshot.mode}`);

    // Restore plugin state
    if (this.originalSnapshot.pluginEnabled) {
      await this.enablePlugin();
    } else {
      await this.disablePlugin();
    }

    // Restore pro credentials
    if (this.originalSnapshot.proEnabled) {
      await this.restoreProCredentials();
    }

    this.log('Configuration restored');
    this.originalSnapshot = null;
  }

  /**
   * Run a function with a specific mode, then restore original state
   */
  async withMode<T>(mode: BenchmarkMode, fn: () => Promise<T>): Promise<T> {
    await this.saveSnapshot();
    try {
      await this.switchMode(mode);
      return await fn();
    } finally {
      await this.restore();
    }
  }
}

/**
 * Create a config switcher with default options
 */
export function createConfigSwitcher(options?: ConfigSwitcherOptions): ConfigSwitcher {
  return new ConfigSwitcher(options);
}

/**
 * Quick check if PopKit is available for benchmarking
 */
export async function isPopKitAvailable(): Promise<{
  installed: boolean;
  enabled: boolean;
  proConfigured: boolean;
}> {
  const switcher = new ConfigSwitcher();
  const pluginsDir = join(homedir(), '.claude', 'plugins', 'marketplaces');
  const pluginPath = join(pluginsDir, 'popkit-marketplace');
  const disabledPath = join(pluginsDir, 'popkit-marketplace.disabled');

  const enabled = await switcher.isPluginEnabled();
  const proConfigured = await switcher.isProEnabled();

  // Check if installed (either enabled or disabled)
  let installed = enabled;
  if (!installed) {
    try {
      await access(disabledPath);
      installed = true;
    } catch {
      installed = false;
    }
  }

  return { installed, enabled, proConfigured };
}
