using System.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using SteamHeatmap.Web.Domain;
using SteamHeatmap.Web.Models;

namespace SteamHeatmap.Web.Controllers;

public class HomeController : Controller
{
    private readonly RegionMapViewModelBuilder _viewModelBuilder;

    public HomeController(RegionMapViewModelBuilder viewModelBuilder)
    {
        _viewModelBuilder = viewModelBuilder;
    }

    public async Task<IActionResult> Index()
    {
        var viewModel = await _viewModelBuilder.Build();
        return View(viewModel);
    }

    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public IActionResult Error()
    {
        return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
    }
}
