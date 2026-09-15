source "https://rubygems.org"

# Modern build stack (post-fastpages migration): jekyll 4.3 + current gems.
# Notebooks are converted by the fastpages converter action (Python), which is
# independent of this Gemfile.

gem "jekyll", "~> 4.3"
# Theme: pinned minima fork (provides assets/css/style.scss + skins), fetched
# at build time by jekyll-remote-theme. The minima gem is declared because
# _config.yml also sets `theme: minima` (remote_theme takes precedence).
gem "minima"

group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-gist"
  gem "jekyll-octicons"
  gem "jekyll-remote-theme"
  gem "jekyll-twitter-plugin"
  gem "jekyll-relative-links"
  gem "jekyll-seo-tag"
  gem "jekyll-redirect-from"
  gem "jekyll-toc"
  gem "jekyll-paginate"
  gem "jekyll-sitemap"
  gem "jemoji"
end

gem "kramdown-math-katex"
gem "webrick"

# Performance-booster for watching directories on Windows
gem "wdm", :install_if => Gem.win_platform?
