import { Controller, Get, Post, Put, Param, Body, Request, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { SuggestionsService } from './suggestions.service';

@Controller('suggestions')
@UseGuards(JwtAuthGuard)
export class SuggestionsController {
  constructor(private suggestionsService: SuggestionsService) {}

  @Get()
  list(@Request() req) {
    return this.suggestionsService.getSuggestions(req.user.userId);
  }

  @Post('import')
  importFiles(@Request() req) {
    return this.suggestionsService.importFromFiles(req.user.userId);
  }

  @Post('search')
  triggerSearch(
    @Request() req,
    @Body('keywords') keywords?: string,
    @Body('country') country?: string,
  ) {
    return this.suggestionsService.triggerSearch(req.user.userId, keywords, country);
  }

  @Post('trigger-action')
  triggerAction(
    @Body('keywords') keywords?: string,
    @Body('location') location?: string,
  ) {
    return this.suggestionsService.triggerGitHubAction(keywords, location);
  }

  @Post(':id/add-to-wishlist')
  addToWishlist(@Request() req, @Param('id') id: string) {
    return this.suggestionsService.addToWishlist(req.user.userId, parseInt(id));
  }

  @Put(':id/dismiss')
  dismiss(@Request() req, @Param('id') id: string) {
    return this.suggestionsService.dismiss(req.user.userId, parseInt(id));
  }
}
