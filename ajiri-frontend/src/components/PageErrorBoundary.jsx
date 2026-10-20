import { Component } from 'react'

// Old tabs can request a lazy chunk removed by a release. Offer an explicit reload
// instead of a blank page or automatic retries of user mutations.
// see docs/CONCEPTS.md#updated-page-recovery
export default class PageErrorBoundary extends Component {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    if (!this.state.failed) return this.props.children
    return <main className="page stack" aria-labelledby="page-recovery-heading">
      <h1 id="page-recovery-heading">This page could not load</h1>
      <p>A newer version may be available, or your connection may have been interrupted.</p>
      <p>Reload to continue. Unsaved edits may be lost. No application is sent by reloading.</p>
      <button className="btn" onClick={this.props.onReload || (() => window.location.reload())}>Reload application</button>
    </main>
  }
}
