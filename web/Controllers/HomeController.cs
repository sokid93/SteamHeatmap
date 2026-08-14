using System.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using SteamHeatmap.Web.Domain;
using SteamHeatmap.Web.Models;

namespace SteamHeatmap.Web.Controllers;

public class HomeController : Controller
{
    private readonly RegionMapViewModelBuilder _viewModelBuilder;
    private readonly CatalogSearchViewModelBuilder _catalogSearchBuilder;

    public HomeController(
        RegionMapViewModelBuilder viewModelBuilder, CatalogSearchViewModelBuilder catalogSearchBuilder)
    {
        _viewModelBuilder = viewModelBuilder;
        _catalogSearchBuilder = catalogSearchBuilder;
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

    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public IActionResult Error()
    {
        return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
    }
}
