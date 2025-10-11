/**
 * Example usage of secure output encoding components
 * 
 * This file demonstrates how to use the SafeHtml, SafeText, and SafeLink
 * components to prevent XSS attacks while still allowing safe HTML formatting.
 */

import React from 'react';
import { SafeHtml, SafeText, SafeLink } from './output-encoding';

interface SecurityDemoProps {
  userContent: string;
  userLink: string;
}

export function SecurityDemo({ userContent, userLink }: SecurityDemoProps) {
  // Examples of potentially dangerous user input
  const dangerousContent = `
    <p>This is safe content</p>
    <script>alert('XSS Attack!');</script>
    <img src="x" onerror="alert('Image XSS')">
    <div onclick="alert('Click XSS')">Click me</div>
  `;

  const dangerousLinks = [
    'javascript:alert("XSS")',
    'data:text/html,<script>alert("XSS")</script>',
    'https://legitimate-site.com',
    '/internal/path',
  ];

  return (
    <div className="security-demo">
      <h2>Security Demo: Safe Content Rendering</h2>
      
      {/* Example 1: Safe HTML rendering with different security levels */}
      <section>
        <h3>SafeHtml Component Examples</h3>
        
        <div className="demo-section">
          <h4>Strict Level (only basic text formatting)</h4>
          <SafeHtml 
            html={dangerousContent} 
            level="strict" 
            className="content-strict"
          />
        </div>

        <div className="demo-section">
          <h4>Basic Level (common formatting tags)</h4>
          <SafeHtml 
            html={dangerousContent} 
            level="basic" 
            className="content-basic"
          />
        </div>

        <div className="demo-section">
          <h4>Rich Level (rich formatting including images)</h4>
          <SafeHtml 
            html={dangerousContent} 
            level="rich" 
            className="content-rich"
          />
        </div>
      </section>

      {/* Example 2: Safe text rendering */}
      <section>
        <h3>SafeText Component Example</h3>
        <p>User input: 
          <SafeText 
            text={`<script>alert('This will be escaped')</script>`}
            className="user-input"
          />
        </p>
      </section>

      {/* Example 3: Safe link rendering */}
      <section>
        <h3>SafeLink Component Examples</h3>
        {dangerousLinks.map((link, index) => (
          <div key={index} className="link-demo">
            <p>Original URL: <code>{link}</code></p>
            <SafeLink href={link} className="demo-link">
              Test Link {index + 1}
            </SafeLink>
          </div>
        ))}
      </section>

      {/* Example 4: User-provided content */}
      <section>
        <h3>User Content Example</h3>
        <SafeHtml 
          html={userContent} 
          level="basic"
          className="user-content"
        />
        
        <SafeLink href={userLink} target="_blank">
          User-provided link
        </SafeLink>
      </section>

      {/* Example 5: Form content example */}
      <section>
        <h3>Form Content Safety</h3>
        <p>The following demonstrates how form content should be handled:</p>
        
        {/* Safe way to display form data */}
        <div className="form-display">
          <p><strong>Name:</strong> <SafeText text="<script>alert('name')</script>" /></p>
          <p><strong>Bio:</strong> 
            <SafeHtml 
              html="<p>I'm a developer who loves <strong>React</strong> and <em>security</em>!</p><script>alert('bio')</script>"
              level="basic"
            />
          </p>
        </div>
      </section>

      <style jsx>{`
        .security-demo {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }

        .demo-section {
          margin: 20px 0;
          padding: 15px;
          border: 1px solid #ddd;
          border-radius: 5px;
          background: #f9f9f9;
        }

        .link-demo {
          margin: 10px 0;
          padding: 10px;
          background: #fff;
          border-radius: 3px;
        }

        .content-strict {
          background: #ffe6e6;
        }

        .content-basic {
          background: #fff3cd;
        }

        .content-rich {
          background: #d4edda;
        }

        .user-input {
          background: #e2e3e5;
          padding: 2px 5px;
          font-family: monospace;
        }

        .demo-link {
          display: inline-block;
          padding: 5px 10px;
          margin: 5px 0;
          background: #007bff;
          color: white;
          text-decoration: none;
          border-radius: 3px;
        }

        .demo-link:hover {
          background: #0056b3;
        }

        .form-display {
          background: #f8f9fa;
          padding: 15px;
          border-radius: 5px;
          margin: 10px 0;
        }

        code {
          background: #f1f3f4;
          padding: 2px 4px;
          border-radius: 3px;
          font-family: monospace;
        }
      `}</style>
    </div>
  );
}

export default SecurityDemo;