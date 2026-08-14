using System.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using SteamHeatmap.Web.Domain;
using SteamHeatmap.Web.Models;

namespace SteamHeatmap.Web.Controllers;

public class HomeController : Controller
{
    private readonly RegionMapViewModelBuilder _viewModelBuilder;
    private readonly CatalogSearchViewModelBuilder _catalogSearchBuilder;
    private readonly OnDemandGameFetcher _onDemandGameFetcher;

    public HomeController(
        RegionMapViewModelBuilder viewModelBuilder,
        CatalogSearchViewModelBuilder catalogSearchBuilder,
        OnDemandGameFetcher onDemandGameFetcher)
    {
        _viewModelBuilder = viewModelBuilder;
        _catalogSearchBuilder = catalogSearchBuilder;
        _onDemandGameFetcher = onDemandGameFetcher;
    }

    public async Task<IActionResult> Index()
    {
        var viewModel = await _viewModelBuilder.Build();
        return View(viewModel);
    }

    // #26: full-catalog search, supplementing #14's embedded-dataset typeahead
    // once the local match set runs thin. q defaults to "" (not required) so
    // a bare/malformed request degrades to an empty result list, not a 400.
    [HttpGet]
    public async Task<IActionResult> SearchCatalog(string q = "")
    {
        var results = await _catalogSearchBuilder.Search(q);
        return Json(results.Select(r => new { appId = r.AppId, name = r.Name }));
    }

    // #27: selecting an untracked search result. Live, request-scoped Steam
    // calls (ADR-006 amendment) — POST because it writes region_scores/games,
    // not idempotent-safe-to-cache like a GET search.
    [HttpPost]
    public async Task<IActionResult> FetchGame(int appId)
    {
        var result = await _onDemandGameFetcher.Fetch(appId);
        if (!result.HasEnoughReviews)
            return Json(new { hasEnoughReviews = false });

        return Json(new
        {
            hasEnoughReviews = true,
            appId,
            name = result.GameName,
            concentrations = result.RegionScores.ToDictionary(s => s.RegionCode, s => s.Concentration),
        });
    }

    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public IActionResult Error()
    {
        return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
    }
}
