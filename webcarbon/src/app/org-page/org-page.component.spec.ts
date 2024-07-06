import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OrgPageComponent } from './org-page.component';

describe('OrgPageComponent', () => {
  let component: OrgPageComponent;
  let fixture: ComponentFixture<OrgPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OrgPageComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(OrgPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
